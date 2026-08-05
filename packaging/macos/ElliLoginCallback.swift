import AppKit
import Foundation

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationWillFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.prohibited)
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        guard let callbackURL = urls.first else {
            application.terminate(nil)
            return
        }
        let distributionDirectory = Bundle.main.bundleURL.deletingLastPathComponent()
        let executable = distributionDirectory.appendingPathComponent("elli-billing-tool.exec")
        let process = Process()
        process.executableURL = executable
        process.arguments = ["oauth-callback", callbackURL.absoluteString]
        process.currentDirectoryURL = distributionDirectory
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        try? process.run()
        application.terminate(nil)
    }
}

let application = NSApplication.shared
let delegate = AppDelegate()
application.delegate = delegate
application.run()
