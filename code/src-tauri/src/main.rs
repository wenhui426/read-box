// Read-Box Tauri 桌面应用入口
// 调用 lib.rs 中的 run() 函数启动应用
// release 模式下隐藏 Windows 控制台窗口

// 在 release 模式下隐藏 Windows 控制台窗口
// 防止用户看到命令行窗口
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    // 委托给 lib.rs 中的 run() 函数
    // 具体逻辑（后端进程管理、窗口事件）在 lib.rs 中实现
    read_box_lib::run();
}
