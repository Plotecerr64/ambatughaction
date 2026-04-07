"""
A small Qt adapter that mimics the QWebEngineView API subset used by
typical browser-like apps.

This wraps `webviewpy.Webview` inside a QWidget so you can migrate code like:

    from PyQt6.QtWebEngineWidgets import QWebEngineView

to:

    from webviewpy_adapter import QWebEngineView

"""

from dataclasses import dataclass
from typing import Optional, cast
from ctypes import c_void_p
from PyQt6 import sip
from PyQt6.QtCore import QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QResizeEvent, QWindow
from PyQt6.QtWidgets import QWidget
from html.parser import HTMLParser
from webviewpy import Webview, webview_native_handle_kind_t


##import ##logging
##from datetime import datetime
##class MicrosecondFormatter(##logging.Formatter):
##    def formatTime(self, record, datefmt=None):
##        dt = datetime.fromtimestamp(record.created)
##        if datefmt:
##            return dt.strftime(datefmt)
##        else:
##            return dt.strftime("%H:%M:%S.%f")  # default with microseconds
##logger = ##logging.getLogger()
##logger.setLevel(##logging.DEBUG)
##ch = ##logging.StreamHandler()
##formatter = MicrosecondFormatter(fmt='%(asctime)s [%(threadName)s] %(message)s')
##ch.setFormatter(formatter)
##logger.addHandler(ch)

JS_BOOTSTRAP = r"""
(() => {
  if (window.__qt_webviewpy_adapter_installed) return;
  window.__qt_webviewpy_adapter_installed = true;

  /* Force new tab to open inside current WebView tab */
  /* Prefer intercepting behavior instead of mutating DOM */

  document.addEventListener('click', (e) => {
    if (
      e.defaultPrevented ||
      e.button === 1 ||     // middle click
      e.ctrlKey             // Ctrl/Cmd + left click
    ) return;
    if (e.target instanceof HTMLElement) {
      const el = e.target.closest("a, area");
      if (!el) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      window.location.href = el.href;
      notify();
    }
  }, true);

  (() => {
    const origSubmit = HTMLFormElement.prototype.submit;
    HTMLFormElement.prototype.submit = function () {
      this.target = "_self";
      return origSubmit.apply(this, arguments);
    };
  })();

  document.addEventListener("submit", (e) => {
    if (e.target instanceof HTMLFormElement) {
      e.preventDefault();
      e.target.submit();
    }
  }, true);

  Object.defineProperty(window, "open", {
    configurable: false,
    writable: false,
    value: (url) => {
      if (url) {
        window.location.href = url.toString();
      }
      return window;
    }
  });

  /* Notify URL or title changes */

  let __lastUrl = ""; let __lastTitle = "";
  const notify = () => {
    const __url = location.href;
    const __title = document.title;
    if (
      __url === __lastUrl &&
      __title === __lastTitle
    ) return;
    __lastUrl = __url;
    __lastTitle = __title;
    try {
      const __seq = Number(window.__qt_nav_seq || 0);
      window.__qt_sync_state(__seq, __url, __title);
    } catch (e) {
      // Best effort only.
    }
  };

  (() => {
    const pushState = history.pushState;
    const replaceState = history.replaceState;
    history.pushState = function (...args) {
      const r = pushState.apply(this, args);
      notify();
      return r;
    };
    history.replaceState = function (...args) {
      const r = replaceState.apply(this, args);
      notify();
      return r;
    };
  })();

  new MutationObserver(notify).observe(
    document.head, { childList: true, subtree: true }
  );

  window.addEventListener('load', notify);
  window.addEventListener('pageshow', notify);
  window.addEventListener('hashchange', notify);
  window.addEventListener('popstate', notify);
  notify();
})();
"""


@dataclass
class QWebEnginePage:
    """Minimal QWebEngineView.page()-like object."""

    owner: "QWebEngineView"

    def load(self, url: QUrl) -> None:
        return self.owner.load(url)

    def setUrl(self, url: QUrl) -> None:
        return self.owner.setUrl(url)

    def setHtml(self, html: Optional[str], baseUrl: QUrl = QUrl()) -> None:
        return self.owner.setHtml(html, baseUrl)

    def url(self) -> QUrl:
        return self.owner.url()

    def title(self) -> str:
        return self.owner.title()

    def requestedUrl(self) -> QUrl:
        return self.owner._requested_url

    def runJavaScript(self, scriptSource: Optional[str]) -> None:
        self.owner._eval_js(scriptSource or "")


class QWebEngineView(QWidget):
    """
    A QWidget-based drop-in replacement for the common
    QWebEngineView API.

    Notes:
    This is not a full QWebEngineView replacement;
    it covers the browser-like methods and signals used in
    typical browser-like apps.
    """

    urlChanged = pyqtSignal(QUrl)
    titleChanged = pyqtSignal(str)
    loadStarted = pyqtSignal()
    loadFinished = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None, *, debug: bool = False):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)

        self._debug = debug
        self._webview: Optional[Webview] = None
        self._qwin: Optional[QWindow] = None
        self._page_proxy = QWebEnginePage(self)

        self._requested_url = QUrl()
        self._current_url = QUrl()
        self._current_title = ""

        self._pending_url = QUrl()
        self._pending_html: Optional[str] = None
        self._pending_base_url = QUrl()

        self._nav_seq = 0
        self._active_nav_seq = 0
        self._loading_nav_seq = 0
        self._load_in_progress = False

        self._bootstrapped = False

        # Create the underlying native webview after Qt has established a window
        # handle for this widget.
        QTimer.singleShot(0, self._bootstrap)

    # ----- QWebEngineView-ish API -----

    def load(self, url: QUrl) -> None:
        ##logging.debug(f"load() called with :{url.toString()}")
        # Invalidate previous navigation
        self._nav_seq += 1
        seq = self._nav_seq
        self._active_nav_seq = seq

        self._requested_url = QUrl(url)
        self._pending_url = QUrl(url)
        self._pending_html = None
        self._pending_base_url = QUrl()

        self.urlChanged.emit(url)
        self.loadStarted.emit()

        ##if self._webview is None:
        ##    ##logging.debug(f"load() pending until bootstrap: {url.toString()}")
        ##    return

        ##logging.debug(f"load() _load_in_progress is {self._load_in_progress}")
        if self._load_in_progress:
            self.stop()
        self._flush_pending()

    def setUrl(self, url: QUrl) -> None:
        self.load(url)

    def setHtml(self, html: Optional[str], baseUrl: QUrl = QUrl()) -> None:
        # this function haven't been tested btw
        self._nav_seq += 1
        seq = self._nav_seq
        self._active_nav_seq = seq

        self._pending_url = QUrl()
        self._pending_html = html or ""
        self._pending_base_url = baseUrl

        self.loadStarted.emit()

        ##if self._webview is None:
        ##    return

        ##logging.debug(f"setHtml() _load_in_progress is {self._load_in_progress}")
        if self._load_in_progress:
            self.stop()
        self._flush_pending()

    def url(self) -> QUrl:
        return QUrl(self._current_url)

    def title(self) -> str:
        return self._current_title

    def page(self) -> QWebEnginePage:
        return self._page_proxy

    def back(self) -> None:
        self._eval_js("history.back()")

    def forward(self) -> None:
        self._eval_js("history.forward()")

    def reload(self) -> None:
        self._eval_js("location.reload()")

    def stop(self) -> None:
        self._eval_js("window.stop()")
        ##logging.debug(f"stop() _load_in_progress is {self._load_in_progress}")
        self._load_in_progress = False

    # ----- internals -----

    def _bootstrap(self) -> None:
        if self._bootstrapped:
            return
        self._bootstrapped = True
        ##logging.debug("_bootstrap() starts")

        self._webview = Webview(debug=self._debug, window=c_void_p(int(self.winId())))
        # accept *args because webviewpy doesn't do @typing.overload
        self._webview.bind("__qt_sync_state", lambda *args: self._on_js_sync_state(*args))

        # Keep the adapter informed about URL/title changes. We rely on webviewpy's
        # JS injection hook (`init`) and a bound Python callback, which its PyQt
        # example uses for load notifications.
        self._webview.init(JS_BOOTSTRAP)

        hwnd = self._webview.get_native_handle(
            # Wrap to satisfies type checkers
            webview_native_handle_kind_t(
                webview_native_handle_kind_t.WEBVIEW_NATIVE_HANDLE_KIND_UI_WIDGET
            )
        )
        self._qwin = QWindow.fromWinId(cast(sip.voidptr, hwnd))
        self._sync_native_geometry()
        ##logging.debug("_bootstrap() done")

        # Load the latest pending navigation.
        self._flush_pending()

    def _flush_pending(self) -> None:
        if self._webview is None:
            return
            # will be called again after bootstrap

        if self._pending_url and self._pending_url.isValid():
            url = QUrl(self._pending_url)

            # Consume pending request first to avoids duplicate loads
            self._pending_url = QUrl()
            self._pending_html = None
            self._pending_base_url = QUrl()
            # Now mark that a load is in progress
            ##logging.debug(f"_flush_pending(url) _load_in_progress is {self._load_in_progress}")
            self._load_in_progress = True

            self._loading_nav_seq = self._active_nav_seq
            self._webview.init(f"window.__qt_nav_seq = {self._loading_nav_seq};")

            ##logging.debug(f"Navigating to pending URL: {url.toString()} seq={self._loading_nav_seq}")
            self._webview.navigate(url.toString())
            return

        if self._pending_html is not None:
            html = self._pending_html
            base_url = QUrl(self._pending_base_url)

            self._pending_html = None
            self._pending_base_url = QUrl()
            ##logging.debug(f"_flush_pending(html) _load_in_progress is {self._load_in_progress}")
            self._load_in_progress = True

            self._loading_nav_seq = self._active_nav_seq
            self._webview.init(f"window.__qt_nav_seq = {self._loading_nav_seq};")

            if base_url.isValid():
                rewriter = HtmlUrlRewriter(base_url)
                rewriter.feed(html)
                resolved_html = rewriter.get_html()
            else:
                resolved_html = html

            ##logging.debug(f"Setting pending HTML seq={self._loading_nav_seq}")
            self._webview.set_html(resolved_html)
            return

    def _eval_js(self, script: str) -> None:
        if self._webview is None:
            return
        try:
            self._webview.eval(script)
        except Exception:
            # Keep navigation controls best-effort, like QWebEngineView slots.
            pass

    def _on_js_sync_state(self, nav_seq: int, location: str, title: str) -> None:
        # Ignore stale callbacks from older navigations.
        if nav_seq != self._active_nav_seq:
            ##logging.debug(
            ##    f"Ignoring stale sync state seq={nav_seq}, active={self._active_nav_seq}, url={location}"
            ##)
            return

        ##logging.debug(f"Starting sync state seq={nav_seq}, url={location}")
        qurl = QUrl(location)
        if qurl != self._current_url:
            self._current_url = qurl
            if qurl != self._requested_url:
                self.urlChanged.emit(qurl)

        if title != self._current_title:
            self._current_title = title
            self.titleChanged.emit(title)
            self.setWindowTitle(title or "Browser")

        ##logging.debug(f"_on_js_sync_state() _load_in_progress is {self._load_in_progress}")
        if self._load_in_progress and nav_seq == self._loading_nav_seq:
            self._load_in_progress = False
            self.loadFinished.emit(True)

        ##logging.debug(f"Successful sync state seq={nav_seq}, url={location}")
        # If a newer load() was requested while this page was loading,
        # trigger it now that the current navigation has reached a stable state.
        self._flush_pending()

    def _sync_native_geometry(self) -> None:
        if self._qwin is None:
            return
        self._qwin.setGeometry(self.rect())

    def resizeEvent(self, a0: Optional[QResizeEvent]) -> None:
        super().resizeEvent(a0)
        self._sync_native_geometry()

    @staticmethod
    def version():
        """
        Get the webviewpy library version information.
        """
        return Webview.version()

class HtmlUrlRewriter(HTMLParser):
    """
    Simple parser that rewrites relative URLs in HTML to absolute URLs
    based on a baseUrl (like QWebEngineView would do).
    """
    def __init__(self, base_url: QUrl):
        super().__init__()
        self.base_url = base_url
        self.result = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "img" and "src" in attrs_dict:
            attrs_dict["src"] = self._resolve_url(attrs_dict["src"])
        elif tag == "script" and "src" in attrs_dict:
            attrs_dict["src"] = self._resolve_url(attrs_dict["src"])
        elif tag == "link" and "href" in attrs_dict:
            attrs_dict["href"] = self._resolve_url(attrs_dict["href"])

        # rebuild tag
        attrs_str = " ".join(f'{k}="{v}"' for k, v in attrs_dict.items())
        self.result.append(f"<{tag} {attrs_str}>")

    def handle_endtag(self, tag):
        self.result.append(f"</{tag}>")

    def handle_data(self, data):
        self.result.append(data)

    def handle_comment(self, data):
        self.result.append(f"<!--{data}-->")

    def _resolve_url(self, url: str) -> str:
        qurl = QUrl(url)
        if qurl.isRelative() and self.base_url.isValid():
            return self.base_url.resolved(qurl).toString()
        return url

    def get_html(self) -> str:
        return "".join(self.result)

if __name__ == "__main__":
    print(QWebEngineView.version())