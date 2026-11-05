import { useState } from 'react'
import { Link } from 'react-router-dom'

const devices = [
  { id: 1, name: 'Core Switch - Cisco Catalyst 9500', location: 'DC-01 Core Rack', ip: '10.0.0.1', status: 'up', uptime: '99.98%', cpu: 12, mem: 34, model: 'Cisco Catalyst 9500', type: 'switch', icon: 'hub', ports: '48/48', alerts: 0 },
  { id: 2, name: 'Firewall - FortiGate 200F', location: 'DC-01 Core Rack', ip: '10.0.0.254', status: 'up', uptime: '99.97%', cpu: 24, mem: 58, model: 'FortiGate 200F', type: 'firewall', icon: 'security', ports: 'N/A', alerts: 0 },
  { id: 3, name: 'Router Gateway - Cisco ASR 1001', location: 'DC-01 ISP Rack', ip: '203.113.0.1', status: 'warning', uptime: '98.42%', cpu: 71, mem: 82, model: 'Cisco ASR 1001-X', type: 'router', icon: 'router', ports: '4/4', alerts: 2 },
  { id: 4, name: 'Access Switch Tầng 3 Block B', location: 'Tầng 3 - Block B', ip: '192.168.3.1', status: 'down', uptime: '0%', cpu: 0, mem: 0, model: 'Cisco Catalyst 2960X', type: 'switch', icon: 'hub', ports: '0/48', alerts: 5 },
  { id: 5, name: 'Wi-Fi Controller - Aruba', location: 'Server Room 02', ip: '192.168.1.100', status: 'up', uptime: '99.95%', cpu: 18, mem: 45, model: 'Aruba 7210', type: 'wireless', icon: 'wifi', ports: '142/145 APs', alerts: 0 },
  { id: 6, name: 'VPN Concentrator', location: 'DMZ Zone', ip: '203.113.0.10', status: 'up', uptime: '99.90%', cpu: 35, mem: 60, model: 'Cisco ASA 5516', type: 'vpn', icon: 'vpn_lock', ports: '220 sessions', alerts: 1 },
]

const alerts = [
  { id: 1, severity: 'critical', icon: 'crisis_alert', title: 'Thiết bị mất phản hồi SNMP', device: 'Access Switch Tầng 3 Block B', time: '09:14', detail: 'Không nhận được SNMP heartbeat trong 5 phút liên tiếp. Ping timeout 100%. Ticket #TK-8901 đã được tạo tự động.' },
  { id: 2, severity: 'warning', icon: 'warning', title: 'CPU cao bất thường trên Router Gateway', device: 'Cisco ASR 1001-X', time: '10:02', detail: 'CPU 71% (ngưỡng cảnh báo: 70%). Khả năng xử lý BGP route table quá tải. Đang giám sát thêm.' },
  { id: 3, severity: 'warning', icon: 'vpn_key_off', title: 'VPN Tunnel với chi nhánh Hà Nội bị ngắt', device: 'VPN Concentrator ASA5516', time: '11:30', detail: 'IPSec tunnel HN-01 flapping liên tục. DPD failure. Có thể do mất gói tin phía ISP chi nhánh.' },
  { id: 4, severity: 'info', icon: 'info', title: 'Firmware cũ phát hiện trên 3 Access Point', device: 'Aruba 7210 Controller', time: '08:00', detail: 'AP-B2-05, AP-B2-06, AP-B3-11 đang chạy firmware v8.9.0 (cũ). Phiên bản mới v8.11 đã sẵn sàng.' },
]

const SEVERITY_STYLES = {
  critical: { bg: 'bg-[#ffdad6]', text: 'text-[#ba1a1a]', border: 'border-[#ba1a1a]', dot: 'bg-[#ba1a1a]' },
  warning: { bg: 'bg-[#fffbeb]', text: 'text-[#b45309]', border: 'border-[#f59e0b]', dot: 'bg-[#f59e0b]' },
  info: { bg: 'bg-[#eff4ff]', text: 'text-[#004ac6]', border: 'border-[#004ac6]', dot: 'bg-[#004ac6]' },
}

const STATUS_STYLES = {
  up: { label: 'Hoạt động', dot: 'bg-[#22c55e]', text: 'text-[#15803d]', bg: 'bg-[#f0fdf4]' },
  warning: { label: 'Cảnh báo', dot: 'bg-[#f59e0b]', text: 'text-[#b45309]', bg: 'bg-[#fffbeb]', pulse: true },
  down: { label: 'Mất liên lạc', dot: 'bg-[#ba1a1a]', text: 'text-[#ba1a1a]', bg: 'bg-[#ffdad6]', pulse: true },
}

function DeviceCard({ device }) {
  const st = STATUS_STYLES[device.status]
  const cpuColor = device.cpu > 80 ? 'bg-[#ba1a1a]' : device.cpu > 60 ? 'bg-[#f59e0b]' : 'bg-[#004ac6]'
  const memColor = device.mem > 80 ? 'bg-[#ba1a1a]' : device.mem > 60 ? 'bg-[#f59e0b]' : 'bg-[#565e74]'

  return (
    <div className={`bg-white rounded-xl p-4 shadow-sm border-l-4 ${device.status === 'down' ? 'border-[#ba1a1a]' : device.status === 'warning' ? 'border-[#f59e0b]' : 'border-[#004ac6]'} hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${device.status === 'down' ? 'bg-[#ffdad6] text-[#ba1a1a]' : 'bg-[#dce9ff] text-[#004ac6]'}`}>
            <span className="material-symbols-outlined text-[22px]">{device.icon}</span>
          </div>
          <div className="min-w-0">
            <div className="text-[14px] font-semibold text-[#0b1c30] truncate max-w-[200px]">{device.name}</div>
            <div className="font-mono text-[11px] text-[#565e74]">{device.model}</div>
          </div>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${st.bg}`}>
          <span className={`w-2 h-2 rounded-full ${st.dot} ${st.pulse ? 'animate-pulse' : ''}`}></span>
          <span className={`text-[11px] font-semibold ${st.text}`}>{st.label}</span>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-[12px]">
          <span className="text-[#565e74]">IP Address</span>
          <span className="font-mono font-semibold text-[#004ac6]">{device.ip}</span>
        </div>
        <div className="flex items-center justify-between text-[12px]">
          <span className="text-[#565e74]">Vị trí</span>
          <span className="font-semibold text-[#0b1c30]">{device.location}</span>
        </div>
        <div className="flex items-center justify-between text-[12px]">
          <span className="text-[#565e74]">Uptime</span>
          <span className={`font-mono font-bold ${device.uptime === '0%' ? 'text-[#ba1a1a]' : 'text-[#004ac6]'}`}>{device.uptime}</span>
        </div>
        {device.status !== 'down' && (
          <>
            <div>
              <div className="flex items-center justify-between text-[12px] mb-1">
                <span className="text-[#565e74]">CPU</span>
                <span className="font-mono font-semibold text-[#0b1c30]">{device.cpu}%</span>
              </div>
              <div className="w-full bg-[#dce9ff] h-1.5 rounded-full">
                <div className={`${cpuColor} h-full rounded-full`} style={{ width: `${device.cpu}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between text-[12px] mb-1">
                <span className="text-[#565e74]">Memory</span>
                <span className="font-mono font-semibold text-[#0b1c30]">{device.mem}%</span>
              </div>
              <div className="w-full bg-[#dce9ff] h-1.5 rounded-full">
                <div className={`${memColor} h-full rounded-full`} style={{ width: `${device.mem}%` }}></div>
              </div>
            </div>
          </>
        )}
        <div className="flex items-center justify-between text-[12px]">
          <span className="text-[#565e74]">Ports / Connections</span>
          <span className="font-mono text-[#0b1c30]">{device.ports}</span>
        </div>
      </div>

      {device.alerts > 0 && (
        <div className="mt-3 pt-3 border-t border-[#eff4ff] flex items-center justify-between">
          <span className="text-[11px] text-[#ba1a1a] font-semibold flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">warning</span>
            {device.alerts} cảnh báo đang hoạt động
          </span>
          <Link to={`/tickets?device=${device.ip}`}>
            <button className="text-[11px] text-[#004ac6] hover:underline font-semibold">Xem Ticket →</button>
          </Link>
        </div>
      )}
    </div>
  )
}

function AlertRow({ alert }) {
  const st = SEVERITY_STYLES[alert.severity]
  return (
    <div className={`flex gap-3 p-3 rounded-xl border ${st.bg} border-${st.border}`}>
      <div className={`w-9 h-9 rounded-full ${st.bg} ${st.text} flex items-center justify-center flex-shrink-0`}>
        <span className="material-symbols-outlined text-[18px]">{alert.icon}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <span className={`text-[13px] font-semibold ${st.text}`}>{alert.title}</span>
          <span className="font-mono text-[11px] text-[#737686]">{alert.time}</span>
          <span className={`text-[11px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded ${st.bg} ${st.text}`}>
            {alert.severity}
          </span>
        </div>
        <div className="text-[12px] text-[#565e74] font-mono mb-1">{alert.device}</div>
        <div className="text-[13px] text-[#434655]">{alert.detail}</div>
      </div>
    </div>
  )
}

export default function NetworkOps() {
  const [view, setView] = useState('grid')
  const [filter, setFilter] = useState('all')

  const filteredDevices = filter === 'all' ? devices : devices.filter(d => d.status === filter)

  const upCount = devices.filter(d => d.status === 'up').length
  const warnCount = devices.filter(d => d.status === 'warning').length
  const downCount = devices.filter(d => d.status === 'down').length

  return (
    <div className="px-5 py-5 space-y-5 max-w-[1680px] mx-auto w-full">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl shadow-sm">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#dce9ff] text-[#004ac6] font-mono text-[11px] font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#004ac6] animate-ping"></span>
                NETWORK OPERATIONS CENTER • LIVE
              </span>
            </div>
            <h1 className="text-[28px] font-bold text-[#0b1c30] tracking-tight">Network Operations Center</h1>
            <p className="text-[14px] text-[#565e74]">Giám sát trực tiếp toàn bộ thiết bị mạng, cảnh báo và tình trạng hạ tầng</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-[#004ac6] text-white hover:bg-[#0051b1] transition-colors shadow-sm text-[12px] font-semibold">
              <span className="material-symbols-outlined text-[18px]">refresh</span>
              <span>Làm mới</span>
            </button>
            <button className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-[#eff4ff] text-[#0b1c30] hover:bg-[#dce9ff] transition-colors text-[12px] font-semibold">
              <span className="material-symbols-outlined text-[18px]">download</span>
              <span>Xuất báo cáo</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Thiết bị Hoạt động', value: upCount, icon: 'check_circle', bg: 'bg-[#f0fdf4]', iconColor: 'text-[#22c55e]', textColor: 'text-[#15803d]' },
          { label: 'Cảnh báo', value: warnCount, icon: 'warning', bg: 'bg-[#fffbeb]', iconColor: 'text-[#f59e0b]', textColor: 'text-[#b45309]' },
          { label: 'Mất liên lạc', value: downCount, icon: 'error', bg: 'bg-[#ffdad6]', iconColor: 'text-[#ba1a1a]', textColor: 'text-[#ba1a1a]' },
          { label: 'Tổng thiết bị', value: devices.length, icon: 'devices', bg: 'bg-[#eff4ff]', iconColor: 'text-[#004ac6]', textColor: 'text-[#0b1c30]' },
        ].map(k => (
          <div key={k.label} className={`${k.bg} p-4 rounded-xl flex items-center gap-3`}>
            <span className={`material-symbols-outlined text-[28px] ${k.iconColor}`}>{k.icon}</span>
            <div>
              <div className={`text-[28px] font-bold ${k.textColor}`}>{k.value}</div>
              <div className="text-[12px] text-[#565e74]">{k.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Device Grid */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#eff4ff]">
          <div>
            <h2 className="text-[16px] font-semibold text-[#0b1c30]">Danh Sách Thiết Bị Mạng</h2>
            <p className="text-[13px] text-[#565e74]">{filteredDevices.length} thiết bị được hiển thị</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Filter */}
            <div className="inline-flex p-1 rounded-xl bg-[#eff4ff]">
              {[
                { key: 'all', label: 'Tất cả' },
                { key: 'up', label: 'Online' },
                { key: 'warning', label: 'Cảnh báo' },
                { key: 'down', label: 'Offline' },
              ].map(f => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-colors ${filter === f.key ? 'bg-white text-[#004ac6] shadow-sm' : 'text-[#565e74] hover:text-[#0b1c30]'}`}
                >
                  {f.label}
                </button>
              ))}
            </div>
            {/* View toggle */}
            <div className="inline-flex p-1 rounded-xl bg-[#eff4ff]">
              <button onClick={() => setView('grid')} className={`p-1.5 rounded-lg transition-colors ${view === 'grid' ? 'bg-white text-[#004ac6] shadow-sm' : 'text-[#565e74]'}`}>
                <span className="material-symbols-outlined text-[18px]">grid_view</span>
              </button>
              <button onClick={() => setView('list')} className={`p-1.5 rounded-lg transition-colors ${view === 'list' ? 'bg-white text-[#004ac6] shadow-sm' : 'text-[#565e74]'}`}>
                <span className="material-symbols-outlined text-[18px]">view_list</span>
              </button>
            </div>
          </div>
        </div>
        <div className="p-4">
          <div className={view === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4' : 'flex flex-col gap-3'}>
            {filteredDevices.map(device => (
              <DeviceCard key={device.id} device={device} />
            ))}
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 flex items-center justify-between border-b border-[#eff4ff]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#ba1a1a] animate-ping"></span>
            <h2 className="text-[16px] font-semibold text-[#0b1c30]">Cảnh Báo Đang Hoạt Động</h2>
            <span className="px-2 py-0.5 rounded-full bg-[#ffdad6] text-[#ba1a1a] font-mono text-[11px] font-bold">{alerts.length} alerts</span>
          </div>
          <button className="text-[13px] text-[#004ac6] hover:underline font-semibold">Xem tất cả →</button>
        </div>
        <div className="p-4 space-y-3">
          {alerts.map(alert => (
            <AlertRow key={alert.id} alert={alert} />
          ))}
        </div>
      </div>

      {/* Bandwidth Monitor */}
      <div className="bg-white rounded-xl shadow-sm p-5">
        <h2 className="text-[16px] font-semibold text-[#0b1c30] mb-4">Giám Sát Băng Thông WAN</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { name: 'WAN 1 - Viettel 1Gbps', usage: 78, up: '420 Mbps', down: '360 Mbps', status: 'up' },
            { name: 'WAN 2 - VNPT 500Mbps (Backup)', usage: 15, up: '45 Mbps', down: '30 Mbps', status: 'up' },
          ].map(wan => (
            <div key={wan.name} className="bg-[#eff4ff] p-4 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[14px] font-semibold text-[#0b1c30]">{wan.name}</span>
                <span className="font-mono text-[11px] font-bold text-[#004ac6]">{wan.usage}% tải</span>
              </div>
              <div className="w-full bg-[#d3e4fe] h-3 rounded-full mb-3 overflow-hidden">
                <div
                  className={`h-full rounded-full ${wan.usage > 80 ? 'bg-[#ba1a1a]' : wan.usage > 60 ? 'bg-[#f59e0b]' : 'bg-[#004ac6]'}`}
                  style={{ width: `${wan.usage}%` }}
                ></div>
              </div>
              <div className="flex items-center justify-between text-[12px] text-[#565e74]">
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px] text-[#004ac6]">upload</span>
                  <span>Upload: <strong>{wan.up}</strong></span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px] text-[#565e74]">download</span>
                  <span>Download: <strong>{wan.down}</strong></span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

