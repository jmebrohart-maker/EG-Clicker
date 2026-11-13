//! Native process launcher. Python owns the desktop UI and platform integrations.
use std::{
    env,
    path::PathBuf,
    process::{Command, ExitCode},
};

fn app_path() -> Result<PathBuf, String> {
    let exe = env::current_exe().map_err(|e| e.to_string())?;
    let dir = exe.parent().ok_or("Launcher has no parent directory")?;
    for base in [
        dir.to_path_buf(),
        dir.join("../.."),
        PathBuf::from(env!("CARGO_MANIFEST_DIR")),
    ] {
        let script = base.join("EG-Clicker.py");
        if script.is_file() {
            return Ok(script);
        }
    }
    Err("Place EG-Clicker.py beside the executable".into())
}

fn run() -> Result<i32, String> {
    let script = app_path()?;
    let python = env::var_os("EG_CLICKER_PYTHON").unwrap_or_else(|| {
        if cfg!(windows) {
            "python".into()
        } else {
            "python3".into()
        }
    });
    let status = Command::new(python)
        .arg(&script)
        .args(env::args_os().skip(1))
        .current_dir(script.parent().unwrap())
        .status()
        .map_err(|e| format!("Cannot start Python GUI: {e}. Install Python 3 and Tkinter."))?;
    Ok(status.code().unwrap_or(1))
}

fn main() -> ExitCode {
    match run() {
        Ok(code) => ExitCode::from(code.clamp(0, 255) as u8),
        Err(e) => {
            eprintln!("EG-Clicker: {e}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn bundled_script_is_found() {
        assert!(super::app_path().unwrap().ends_with("EG-Clicker.py"));
    }
}
