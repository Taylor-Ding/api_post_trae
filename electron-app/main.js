import { app, BrowserWindow, Menu } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import { platform } from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let backendProcess = null;

function startBackend() {
  const pythonExec = platform() === 'win32' ? 'python' : 'python3';
  backendProcess = spawn(pythonExec, [path.join(__dirname, 'backend', 'api_server.py')], {
    cwd: path.join(__dirname, 'backend'),
    stdio: 'inherit'
  });

  backendProcess.on('error', (error) => {
    console.error('启动后端服务失败:', error);
  });

  backendProcess.on('exit', (code) => {
    console.log('后端服务退出，退出码:', code);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1000,
    minHeight: 600,
    title: '数据一致性自动化核对工具',
    icon: path.join(__dirname, 'public', 'favicon.svg'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    }
  });

  const isDev = process.env.NODE_ENV === 'development';
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  mainWindow.webContents.openDevTools({ mode: 'detach' });
}

Menu.setApplicationMenu(null);

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('quit', function () {
  stopBackend();
});