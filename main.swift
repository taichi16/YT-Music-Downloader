import Cocoa
import WebKit

class DragMessageHandler: NSObject, WKScriptMessageHandler {
    weak var window: NSWindow?

    init(window: NSWindow) {
        self.window = window
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "dragWindow", let window = window, let currentEvent = NSApp.currentEvent {
            window.perform(Selector(("performWindowDragWithEvent:")), with: currentEvent)
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var serverProcess: Process?
    var dragHandler: DragMessageHandler?

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMainMenu()
        startBackend()

        // Create sleek native window
        let windowRect = NSRect(x: 0, y: 0, width: 940, height: 820)
        window = NSWindow(
            contentRect: windowRect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.center()
        window.title = "YT Music Downloader"
        window.titlebarAppearsTransparent = true
        window.titleVisibility = .hidden
        window.isMovableByWindowBackground = false
        window.delegate = self
        window.minSize = NSSize(width: 780, height: 620)

        // Webview Configuration
        let config = WKWebViewConfiguration()
        let handler = DragMessageHandler(window: window)
        self.dragHandler = handler
        config.userContentController.add(handler, name: "dragWindow")

        webView = WKWebView(frame: window.contentView!.bounds, configuration: config)
        webView.autoresizingMask = [.width, .height]
        webView.uiDelegate = self
        webView.setValue(false, forKey: "drawsBackground")
        window.contentView!.addSubview(webView)

        loadApp()

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = NSAlert()
        alert.messageText = "YT Music Downloader"
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.addButton(withTitle: "確定")
        alert.runModal()
        completionHandler()
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = NSAlert()
        alert.messageText = "YT Music Downloader"
        alert.informativeText = message
        alert.alertStyle = .warning
        alert.addButton(withTitle: "確定")
        alert.addButton(withTitle: "取消")
        let result = alert.runModal() == .alertFirstButtonReturn
        completionHandler(result)
    }

    func setupMainMenu() {
        let mainMenu = NSMenu()

        // App Menu
        let appMenuItem = NSMenuItem()
        mainMenu.addItem(appMenuItem)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "關於 YT Music Downloader", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "隱藏 YT Music Downloader", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        let hideOthersItem = NSMenuItem(title: "隱藏其他", action: #selector(NSApplication.hideOtherApplications(_:)), keyEquivalent: "h")
        hideOthersItem.keyEquivalentModifierMask = [.command, .option]
        appMenu.addItem(hideOthersItem)
        appMenu.addItem(withTitle: "顯示全部", action: #selector(NSApplication.unhideAllApplications(_:)), keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "結束 YT Music Downloader", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appMenuItem.submenu = appMenu

        // Edit Menu (Enables Command+A, C, V, X, Z system shortcuts in macOS WebKit)
        let editMenuItem = NSMenuItem()
        mainMenu.addItem(editMenuItem)
        let editMenu = NSMenu(title: "編輯")
        editMenu.addItem(withTitle: "復原", action: Selector(("undo:")), keyEquivalent: "z")
        let redoItem = NSMenuItem(title: "重做", action: Selector(("redo:")), keyEquivalent: "Z")
        redoItem.keyEquivalentModifierMask = [.command, .shift]
        editMenu.addItem(redoItem)
        editMenu.addItem(NSMenuItem.separator())
        editMenu.addItem(withTitle: "剪下", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "複製", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "貼上", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "全選", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editMenuItem.submenu = editMenu

        NSApp.mainMenu = mainMenu
    }

    func startBackend() {
        let bundlePath = Bundle.main.bundlePath
        let serverScript = "\(bundlePath)/Contents/Resources/app/backend/server.py"

        let process = Process()
        let venvPython = "/Users/taichi/AI/music/.venv/bin/python3"
        if FileManager.default.fileExists(atPath: venvPython) {
            process.executableURL = URL(fileURLWithPath: venvPython)
            process.arguments = [serverScript, "4567"]
        } else {
            process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            process.arguments = ["python3", serverScript, "4567"]
        }
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = "/Users/taichi/AI/music/.venv/bin:/opt/homebrew/bin:/usr/local/bin:" + (env["PATH"] ?? "")
        process.environment = env

        do {
            try process.run()
            self.serverProcess = process
        } catch {
            print("Failed to run server: \(error)")
        }
    }

    func loadApp() {
        DispatchQueue.global().async {
            for _ in 0..<20 {
                if let url = URL(string: "http://127.0.0.1:4567/api/default-paths") {
                    if let _ = try? Data(contentsOf: url) {
                        break
                    }
                }
                Thread.sleep(forTimeInterval: 0.2)
            }

            DispatchQueue.main.async {
                if let url = URL(string: "http://127.0.0.1:4567") {
                    self.webView.load(URLRequest(url: url))
                }
            }
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        serverProcess?.terminate()
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
