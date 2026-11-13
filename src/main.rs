//! Launch only the Python application packaged beside this executable.
use std::{
    env,
    path::{Path, PathBuf},
    process::{Command, ExitCode},
};

fn app_path_from(exe: &Path) -> Result<PathBuf, String> {
    let script = exe
        .parent()
        .ok_or("Launcher has no parent directory")?
        .join("EG-Clicker.py");
    let regular = script
        .symlink_metadata()
        .map(|m| m.file_type().is_file())
        .unwrap_or(false);
    if regular {
        Ok(script)
    } else {
        Err("Place EG-Clicker.py beside the executable (no symlinks).".into())
    }
}

fn interpreter() -> Result<PathBuf, String> {
    let python = env::var_os("EG_CLICKER_PYTHON")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            if cfg!(windows) {
                PathBuf::from(env::var_os("SystemRoot").unwrap_or_else(|| "C:\\Windows".into()))
                    .join("py.exe")
            } else {
                PathBuf::from("/usr/bin/python3")
            }
        });
    if !python.is_absolute() {
        return Err("EG_CLICKER_PYTHON must be an absolute interpreter path.".into());
    }
    Ok(python)
}

fn run() -> Result<i32, String> {
    let script = app_path_from(&env::current_exe().map_err(|e| e.to_string())?)?;
    let status = Command::new(interpreter()?).arg(&script).args(env::args_os().skip(1))
        .current_dir(script.parent().unwrap()).status()
        .map_err(|e| format!("Cannot start Python GUI: {e}. Install Python 3/Tkinter or set EG_CLICKER_PYTHON to its absolute path."))?;
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
    use super::*;
    use std::{
        fs,
        time::{SystemTime, UNIX_EPOCH},
    };
    #[test]
    fn requires_a_regular_sibling_and_ignores_ancestor_script() {
        let root = env::temp_dir().join(format!(
            "eg-launcher-test-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let dir = root.join("a/b");
        fs::create_dir_all(&dir).unwrap();
        fs::write(root.join("EG-Clicker.py"), "# ancestor must never execute").unwrap();
        assert!(app_path_from(&dir.join("eg-clicker")).is_err());
        fs::write(dir.join("EG-Clicker.py"), "# packaged app").unwrap();
        assert_eq!(
            app_path_from(&dir.join("eg-clicker")).unwrap(),
            dir.join("EG-Clicker.py")
        );
        #[cfg(unix)]
        {
            fs::remove_file(dir.join("EG-Clicker.py")).unwrap();
            std::os::unix::fs::symlink(root.join("EG-Clicker.py"), dir.join("EG-Clicker.py"))
                .unwrap();
            assert!(app_path_from(&dir.join("eg-clicker")).is_err());
        }
        fs::remove_dir_all(root).unwrap();
    }
}
