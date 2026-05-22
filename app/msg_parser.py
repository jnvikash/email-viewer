import logging
import os
import email
from datetime import datetime
from typing import Optional
from email.parser import BytesParser
from email.policy import default

try:
    import extract_msg
    HAS_EXTRACT_MSG = True
except Exception:
    HAS_EXTRACT_MSG = False

log = logging.getLogger(__name__)

_IMPORTANCE_MAP = {
    "0": "low", "low": "low",
    "1": "normal", "normal": "normal",
    "2": "high", "high": "high",
}


def _safe_str(val) -> str:
    if val is None:
        return ""
    try:
        return str(val).strip()
    except Exception:
        return ""


def _parse_date(date_str) -> Optional[str]:
    """Parse email date from string to ISO format."""
    if not date_str:
        return None
    try:
        if isinstance(date_str, datetime):
            return date_str.isoformat()
        # Try parsing RFC 2822 email date
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.isoformat()
    except Exception:
        return None


def _is_ole2_msg(file_path: str) -> bool:
    """Check if file is OLE2 structured storage (.msg format)."""
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(8)
            return magic == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    except Exception:
        return False


def _parse_ole2_msg(file_path: str) -> Optional[dict]:
    """Parse OLE2 structured storage .msg files (Outlook format)."""
    if not HAS_EXTRACT_MSG:
        return None
    try:
        with extract_msg.openMsg(file_path) as msg:
            recipients = []
            try:
                for r in (msg.recipients or []):
                    recipients.append({"name": _safe_str(r.name), "email": _safe_str(r.email)})
            except Exception:
                pass

            importance_raw = _safe_str(getattr(msg, "importance", "normal")).lower()
            importance = _IMPORTANCE_MAP.get(importance_raw, "normal")

            try:
                size_bytes = os.path.getsize(file_path)
            except OSError:
                size_bytes = None

            attach_count = 0
            try:
                attach_count = len(msg.attachments or [])
            except Exception:
                pass

            text_body = ""
            try:
                text_body = _safe_str(msg.body)
            except Exception:
                pass

            return {
                "file_path": file_path,
                "subject": _safe_str(msg.subject),
                "sender_name": _safe_str(msg.senderName),
                "sender_email": _safe_str(msg.senderEmail),
                "recipients": recipients,
                "date_sent": _parse_date(msg.date if hasattr(msg, 'date') else None),
                "has_html_body": 1 if _safe_str(getattr(msg, "htmlBody", None)) else 0,
                "body_preview": text_body[:300],
                "attachment_count": attach_count,
                "size_bytes": size_bytes,
                "importance": importance,
            }
    except Exception as e:
        log.debug("OLE2 parse failed for %s: %s", file_path, e)
        return None


def _parse_mime_msg(file_path: str) -> Optional[dict]:
    """Parse MIME/RFC 822 email files (.msg, .eml, etc)."""
    try:
        with open(file_path, 'rb') as f:
            parser = BytesParser(policy=default)
            msg = parser.parse(f)

        # Extract headers
        subject = _safe_str(msg.get('Subject', ''))
        from_header = _safe_str(msg.get('From', ''))
        sender_email = from_header
        sender_name = ''

        # Parse "Name <email@domain.com>" format
        if '<' in from_header and '>' in from_header:
            parts = from_header.split('<')
            sender_name = parts[0].strip().strip('"')
            sender_email = parts[1].rstrip('>')
        elif '@' in from_header:
            sender_email = from_header
        else:
            sender_email = from_header

        # Parse recipients
        recipients = []
        to_header = msg.get('To', '')
        if to_header:
            for addr_str in to_header.split(','):
                addr_str = addr_str.strip()
                if '<' in addr_str and '>' in addr_str:
                    name = addr_str.split('<')[0].strip().strip('"')
                    email_addr = addr_str.split('<')[1].rstrip('>')
                    recipients.append({"name": name, "email": email_addr})
                elif '@' in addr_str:
                    recipients.append({"name": '', "email": addr_str})

        # Parse date
        date_str = msg.get('Date')
        date_sent = _parse_date(date_str)

        # Check for HTML body
        has_html_body = 0
        html_body = ''
        text_body = ''

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    has_html_body = 1
                    try:
                        html_body = part.get_content()
                    except Exception:
                        pass
                elif part.get_content_type() == 'text/plain' and not text_body:
                    try:
                        text_body = part.get_content()
                    except Exception:
                        pass
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/html':
                has_html_body = 1
                try:
                    html_body = msg.get_content()
                except Exception:
                    pass
            elif content_type == 'text/plain':
                try:
                    text_body = msg.get_content()
                except Exception:
                    pass

        # Fallback: use payload if no parts found
        if not text_body and not html_body:
            payload = msg.get_payload()
            if isinstance(payload, str):
                text_body = payload[:1000]

        body_preview = (html_body or text_body)[:300]

        # Count attachments
        attach_count = 0
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    attach_count += 1

        try:
            size_bytes = os.path.getsize(file_path)
        except OSError:
            size_bytes = None

        # Extract importance/priority
        priority = _safe_str(msg.get('Priority', ''))
        x_priority = _safe_str(msg.get('X-Priority', ''))
        importance = 'normal'
        if x_priority in ('1', '2') or priority.lower() in ('urgent', 'high'):
            importance = 'high'
        elif x_priority in ('4', '5') or priority.lower() in ('low', 'non-urgent'):
            importance = 'low'

        return {
            "file_path": file_path,
            "subject": subject,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "recipients": recipients,
            "date_sent": date_sent,
            "has_html_body": has_html_body,
            "body_preview": body_preview,
            "attachment_count": attach_count,
            "size_bytes": size_bytes,
            "importance": importance,
        }
    except Exception as e:
        log.debug("MIME parse failed for %s: %s", file_path, e)
        return None


def parse_msg_metadata(file_path: str) -> Optional[dict]:
    """Parse .msg file metadata. Handles both OLE2 and MIME formats."""
    try:
        # Try OLE2 format first (binary .msg files)
        if _is_ole2_msg(file_path):
            result = _parse_ole2_msg(file_path)
            if result:
                return result

        # Fall back to MIME format (text-based email files)
        result = _parse_mime_msg(file_path)
        if result:
            return result

        log.warning("Could not parse %s as OLE2 or MIME format", file_path)
        return None
    except Exception as e:
        log.warning("Failed to parse metadata for %s: %s", file_path, e)
        return None


def get_msg_body(file_path: str) -> tuple[str, str]:
    """Returns (html_body, text_body). Either may be empty string. Handles OLE2 and MIME."""
    # Try OLE2 format first
    if _is_ole2_msg(file_path):
        try:
            with extract_msg.openMsg(file_path) as msg:
                html = ""
                try:
                    raw_html = getattr(msg, "htmlBody", None)
                    if raw_html:
                        if isinstance(raw_html, bytes):
                            html = raw_html.decode("utf-8", errors="replace")
                        else:
                            html = str(raw_html)
                except Exception:
                    pass

                text = ""
                try:
                    text = _safe_str(msg.body)
                except Exception:
                    pass

                return html, text
        except Exception as e:
            log.debug("OLE2 body extraction failed for %s: %s", file_path, e)

    # Try MIME format
    try:
        with open(file_path, 'rb') as f:
            parser = BytesParser(policy=default)
            msg = parser.parse(f)

        html = ""
        text = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/html' and not html:
                    try:
                        html = part.get_content()
                    except Exception:
                        pass
                elif content_type == 'text/plain' and not text:
                    try:
                        text = part.get_content()
                    except Exception:
                        pass
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/html':
                try:
                    html = msg.get_content()
                except Exception:
                    pass
            elif content_type == 'text/plain':
                try:
                    text = msg.get_content()
                except Exception:
                    pass

        return html, text
    except Exception as e:
        log.debug("MIME body extraction failed for %s: %s", file_path, e)
        return "", ""


def get_attachment_bytes(file_path: str, attach_index: int) -> Optional[tuple[str, str, bytes]]:
    """Returns (filename, mime_type, data) or None. Handles OLE2 and MIME."""
    # Try OLE2 format first
    if _is_ole2_msg(file_path):
        try:
            with extract_msg.openMsg(file_path) as msg:
                attachments = msg.attachments or []
                if attach_index < 0 or attach_index >= len(attachments):
                    return None
                att = attachments[attach_index]
                filename = _safe_str(getattr(att, "longFilename", None) or getattr(att, "shortFilename", None) or "attachment")
                data = att.data or b""
                mime = _detect_mime(filename, data)
                return filename, mime, data
        except Exception as e:
            log.debug("OLE2 attachment extraction failed for %s idx %d: %s", file_path, attach_index, e)

    # Try MIME format
    try:
        with open(file_path, 'rb') as f:
            parser = BytesParser(policy=default)
            msg = parser.parse(f)

        if not msg.is_multipart():
            return None

        att_idx = 0
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                if att_idx == attach_index:
                    filename = part.get_filename() or f"attachment_{attach_index}"
                    data = part.get_payload(decode=True)
                    mime = _detect_mime(filename, data)
                    return filename, mime, data
                att_idx += 1

        return None
    except Exception as e:
        log.debug("MIME attachment extraction failed for %s idx %d: %s", file_path, attach_index, e)
        return None


def list_attachments(file_path: str) -> list[dict]:
    """List attachments from OLE2 or MIME format."""
    # Try OLE2 format first
    if _is_ole2_msg(file_path):
        try:
            with extract_msg.openMsg(file_path) as msg:
                result = []
                for idx, att in enumerate(msg.attachments or []):
                    try:
                        filename = _safe_str(
                            getattr(att, "longFilename", None) or getattr(att, "shortFilename", None) or "attachment"
                        )
                        data = att.data or b""
                        result.append({
                            "filename": filename,
                            "size": len(data),
                            "mime_type": _detect_mime(filename, data),
                            "attach_index": idx,
                        })
                    except Exception:
                        result.append({"filename": f"attachment_{idx}", "size": 0, "mime_type": "application/octet-stream", "attach_index": idx})
                return result
        except Exception as e:
            log.debug("OLE2 attachment list failed for %s: %s", file_path, e)

    # Try MIME format
    try:
        with open(file_path, 'rb') as f:
            parser = BytesParser(policy=default)
            msg = parser.parse(f)

        result = []
        att_idx = 0
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename() or f"attachment_{att_idx}"
                    data = part.get_payload(decode=True)
                    result.append({
                        "filename": filename,
                        "size": len(data) if data else 0,
                        "mime_type": _detect_mime(filename, data),
                        "attach_index": att_idx,
                    })
                    att_idx += 1
        return result
    except Exception as e:
        log.debug("MIME attachment list failed for %s: %s", file_path, e)
        return []


def _detect_mime(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    EXT_MAP = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "txt": "text/plain",
        "csv": "text/csv",
        "html": "text/html",
        "htm": "text/html",
        "zip": "application/zip",
        "msg": "application/vnd.ms-outlook",
    }
    if ext in EXT_MAP:
        return EXT_MAP[ext]
    try:
        import magic
        return magic.from_buffer(data[:2048], mime=True)
    except Exception:
        return "application/octet-stream"
