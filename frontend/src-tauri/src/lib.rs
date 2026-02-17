use std::sync::atomic::{AtomicU16, Ordering};
use std::sync::Mutex;
use tauri::Emitter;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

static BACKEND_PORT: AtomicU16 = AtomicU16::new(0);
static BACKEND_CHILD: Mutex<Option<CommandChild>> = Mutex::new(None);

#[tauri::command]
fn get_backend_port() -> u16 {
    let port = BACKEND_PORT.load(Ordering::SeqCst);
    if port == 0 {
        8000
    } else {
        port
    }
}

#[tauri::command]
fn terminate_backend() -> Result<(), String> {
    if let Ok(mut guard) = BACKEND_CHILD.lock() {
        if let Some(child) = guard.take() {
            child.kill().map_err(|e| e.to_string())?;
            log::info!("Backend process terminated via command");
        }
    }
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![get_backend_port, terminate_backend])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            #[cfg(not(debug_assertions))]
            {
                let port = match portpicker::pick_unused_port() {
                    Some(p) => p,
                    None => {
                        log::error!("Failed to find an available port, using default 8000");
                        8000
                    }
                };
                BACKEND_PORT.store(port, Ordering::SeqCst);
                log::info!("Assigned dynamic port for backend: {}", port);

                let app_handle = app.handle().clone();
                let shell = app.shell();
                
                match shell.sidecar("backend") {
                    Ok(command) => {
                        match command.spawn() {
                            Ok((mut rx, child)) => {
                                if let Ok(mut guard) = BACKEND_CHILD.lock() {
                                    *guard = Some(child);
                                }
                                
                                tauri::async_runtime::spawn(async move {
                                    while let Some(event) = rx.recv().await {
                                        match event {
                                            CommandEvent::Stdout(line) => {
                                                let log_line = String::from_utf8_lossy(&line).to_string();
                                                log::info!("[Backend] {}", log_line.trim());
                                                let _ = app_handle.emit("py-log", log_line);
                                            }
                                            CommandEvent::Stderr(line) => {
                                                let log_line = String::from_utf8_lossy(&line).to_string();
                                                log::error!("[Backend Error] {}", log_line.trim());
                                                let _ = app_handle.emit("py-error", log_line);
                                            }
                                            CommandEvent::Error(err) => {
                                                log::error!("[Backend Process Error] {}", err);
                                                let _ = app_handle.emit("py-error", format!("Process error: {}", err));
                                            }
                                            CommandEvent::Terminated(payload) => {
                                                log::info!("[Backend] Process terminated with code: {:?}", payload.code);
                                                let _ = app_handle.emit("backend-terminated", payload.code);
                                                if let Ok(mut guard) = BACKEND_CHILD.lock() {
                                                    *guard = None;
                                                }
                                            }
                                            _ => {}
                                        }
                                    }
                                });
                            }
                            Err(e) => {
                                log::error!("Failed to spawn backend sidecar: {}", e);
                            }
                        }
                    }
                    Err(e) => {
                        log::error!("Failed to create sidecar command: {}", e);
                    }
                }
            }

            #[cfg(debug_assertions)]
            {
                log::info!("Running in development mode. Using fixed port 8000 for backend.");
                log::info!("Make sure to start the Python backend manually: python web_server.py");
            }

            Ok(())
        })
        .on_window_event(|_window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                log::info!("Window close requested, terminating backend process...");
                if let Ok(mut guard) = BACKEND_CHILD.lock() {
                    if let Some(child) = guard.take() {
                        let _ = child.kill();
                        log::info!("Backend process terminated");
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
