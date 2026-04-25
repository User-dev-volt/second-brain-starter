"""
notifications.py — Windows Toast notification utility.

Tries win10toast first, falls back to plyer, then to a console print.
Install (pick one): pip install win10toast   OR   pip install plyer

Usage:
    show_windows_toast("Title", "Body text", duration=5)
"""

import sys


def show_windows_toast(title: str, body: str, duration: int = 5) -> bool:
    """
    Display a Windows Toast notification.

    Returns True if a native toast was shown, False if it fell back to console.
    """
    # Attempt 1: win10toast
    try:
        from win10toast import ToastNotifier
        notifier = ToastNotifier()
        notifier.show_toast(title, body, duration=duration, threaded=True)
        return True
    except ImportError:
        pass
    except Exception:
        pass

    # Attempt 2: plyer
    try:
        from plyer import notification
        notification.notify(title=title, message=body, timeout=duration)
        return True
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: print to console (visible when heartbeat runs in a terminal)
    print(f"[NOTIFICATION] {title}: {body}", file=sys.stderr)
    return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Show a Windows toast notification")
    parser.add_argument("title")
    parser.add_argument("body")
    parser.add_argument("--duration", type=int, default=5)
    args = parser.parse_args()

    show_windows_toast(args.title, args.body, args.duration)
