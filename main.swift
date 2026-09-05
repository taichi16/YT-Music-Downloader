import Cocoa
import WebKit

class DraggableWebView: WKWebView {
    // Custom subclass to guarantee smooth window dragging
    override var mouseDownCanMoveWindow: Bool {
        return true
    }
}

class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var serverProcess: Process?

    func applicationDidFinishLaunching(_ notification: Notification) {
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
        window.isMovableByWindowBackground = true
        window.delegate = self
        window.minSize = NSSize(width: 780, height: 620)

        // Webview Configuration with dragging enabled
        let config = WKWebViewConfiguration()
        webView = DraggableWebView(frame: window.contentView!.bounds, configuration: config)
        webView.autoresizingMask = [.width, .height]
        webView.setValue(false, forKey: "drawsBackground")
        window.contentView!.addSubview(webView)

        loadApp()

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func startBackend() {
        let bundlePath = Bundle.main.bundlePath
        let serverScript = "\(bundlePath)/Contents/Resources/app/backend/server.py"
        
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = ["python3", serverScript, "4567"]
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + (env["PATH"] ?? "")
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
