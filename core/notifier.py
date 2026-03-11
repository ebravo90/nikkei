import logging

try:
    from plyer import notification
    _plyer_available = True
except ImportError:
    _plyer_available = False
    logging.warning("[Notifier] Plyer module not found. Native OS notifications disabled.")


def send_os_notification(title: str, message: str) -> None:
    """
    Sends a cross-platform desktop notification using Plyer.
    Gracefully falls back to stdout if the module is missing or rendering fails 
    (e.g. in Headless environments).
    """
    try:
        if _plyer_available:
            notification.notify(
                title=title,
                message=message,
                app_name="Nikkei OS",
                timeout=5  # Display for 5 seconds
            )
        else:
            print(f"[OS Notification Fallback] {title} - {message}")
            
    except Exception as e:
        # Prevent UI/UX notification crashes from halting critical backend execution
        logging.warning(f"[Notifier] Failed to send OS notification: {e}")
        print(f"[OS Notification Fallback] {title} - {message}")
