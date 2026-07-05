// Read-Box 桌面应用主逻辑
// 负责：管理 Python 后端进程的生命周期（启动、健康检查、重启、清理）
// 以及 Tauri 2.x 应用初始化和窗口事件处理

use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

/// 后端进程的全局状态封装
/// 通过 Mutex 保证线程安全，Tauri 管理其生命周期
struct BackendProcess(Mutex<Option<Child>>);

/// 查找系统可用端口
/// 绑定到 127.0.0.1:0 让操作系统自动分配一个空闲端口
fn find_available_port() -> u16 {
    if let Ok(listener) = std::net::TcpListener::bind(("127.0.0.1", 0)) {
        if let Ok(addr) = listener.local_addr() {
            return addr.port();
        }
    }
    8765 // 兜底端口
}

/// 启动 Python 后端进程
/// 使用 `uv run uvicorn` 命令启动 FastAPI 应用
fn start_backend(port: u16) -> Option<Child> {
    let child = Command::new("uv")
        .args([
            "run",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            &port.to_string(),
        ])
        .env("READBOX_PORT", port.to_string())
        .current_dir("../backend")
        .spawn();

    match child {
        Ok(c) => {
            println!("后端已启动，端口: {}，PID: {}", port, c.id());
            Some(c)
        }
        Err(e) => {
            eprintln!("后端启动失败: {}", e);
            None
        }
    }
}

/// 等待后端健康检查通过
/// 每 500ms 轮询一次 /api/health，最多重试 max_retries 次
fn wait_for_backend(port: u16, max_retries: u32) -> bool {
    let url = format!("http://127.0.0.1:{}/api/health", port);
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
        .ok();

    let client = match client {
        Some(c) => c,
        None => return false,
    };

    for attempt in 0..max_retries {
        std::thread::sleep(Duration::from_millis(500));
        if let Ok(resp) = client.get(&url).send() {
            if resp.status().is_success() {
                println!("后端就绪（第 {} 次尝试）", attempt + 1);
                return true;
            }
        }
    }
    false
}

/// 终止后端子进程
/// Windows 使用 taskkill /F 强制终止
/// Unix 使用 kill + wait 优雅终止
fn kill_process(child: &mut Child) {
    #[cfg(target_os = "windows")]
    {
        if let Some(id) = child.id() {
            let _ = Command::new("taskkill")
                .args(["/PID", &id.to_string(), "/F"])
                .spawn();
        }
    }
    #[cfg(not(target_os = "windows"))]
    {
        let _ = child.kill();
        let _ = child.wait();
    }
}

/// Tauri 应用入口
/// 初始化插件、启动后端、配置窗口事件
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // 第一步：分配可用端口
            let port = find_available_port();
            println!("正在启动后端，端口: {}", port);

            // 第二步：启动 Python 后端进程
            let child = start_backend(port);

            // 第三步：等待后端就绪（最多 20 次轮询 ≈ 10 秒）
            if let Some(ref mut c) = child {
                let ready = wait_for_backend(c, 20);
                if ready {
                    println!("后端连接正常");
                } else {
                    eprintln!("后端未能按时就绪");
                }
            }

            // 第四步：保存进程句柄，用于窗口关闭时清理
            app.manage(BackendProcess(Mutex::new(child)));

            // 第五步：将端口号传递给前端
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.eval(&format!(
                    "window.__READBOX_CONFIG__ = {{ port: {} }};",
                    port
                ));
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            // 窗口关闭时自动终止后端进程
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if let Some(state) = window.try_state::<BackendProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            kill_process(child);
                            println!("后端进程已终止");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("Read-Box 启动失败");
}
