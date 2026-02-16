import { useState, useEffect } from 'react'
import { 
  Save, 
  RefreshCw,
  Monitor,
  Bell,
  Clock,
  Globe,
  Eye,
  EyeOff,
  Shield,
  Key,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import { useStore, Config } from '../store'
import { fetchConfig, updateConfig } from '../api'
import clsx from 'clsx'

function TabButton({ 
  label, 
  icon: Icon, 
  active, 
  onClick,
  darkMode = true
}: {
  label: string
  icon: React.ElementType
  active: boolean
  onClick: () => void
  darkMode?: boolean
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ease-smooth',
        active
          ? 'bg-primary-500/10 text-primary-400 border border-primary-500/30'
          : darkMode 
            ? 'text-dark-400 hover:text-dark-100 hover:bg-dark-600/30 border border-transparent'
            : 'text-light-500 hover:text-light-900 hover:bg-light-200 border border-transparent'
      )}
    >
      <Icon size={18} />
      <span className="font-medium text-sm">{label}</span>
    </button>
  )
}

function ConfigSection({
  title,
  icon: Icon,
  iconColor = 'primary',
  children
}: {
  title: string
  icon: React.ElementType
  iconColor?: 'primary' | 'success' | 'warning' | 'danger' | 'cyan'
  children: React.ReactNode
}) {
  const colorClasses = {
    primary: 'text-primary-400',
    success: 'text-success-400',
    warning: 'text-warning-400',
    danger: 'text-danger-400',
    cyan: 'text-cyan-400',
  }

  return (
    <div className="space-y-5">
      <h2 className="section-title">
        <Icon size={18} className={colorClasses[iconColor]} />
        {title}
      </h2>
      {children}
    </div>
  )
}

function FormField({
  label,
  hint,
  children
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {hint && <p className="text-xs text-dark-500 mt-1.5">{hint}</p>}
    </div>
  )
}

function Toggle({
  label,
  description,
  checked,
  onChange,
  icon: Icon,
  iconColor = 'primary',
  darkMode = true
}: {
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
  icon?: React.ElementType
  iconColor?: 'primary' | 'success' | 'warning' | 'neutral'
  darkMode?: boolean
}) {
  const colorClasses = {
    primary: { icon: 'text-primary-400', check: 'bg-primary-400' },
    success: { icon: 'text-success-400', check: 'bg-success-400' },
    warning: { icon: 'text-warning-400', check: 'bg-warning-400' },
    neutral: { icon: darkMode ? 'text-dark-400' : 'text-light-500', check: darkMode ? 'bg-dark-300' : 'bg-light-500' },
  }

  return (
    <label className={clsx(
      'flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all duration-200 border border-transparent',
      darkMode 
        ? 'bg-surface-400/50 hover:bg-surface-400 hover:border-dark-600/50' 
        : 'bg-light-100 hover:bg-light-200 hover:border-light-300'
    )}>
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only"
        />
        <div className={clsx(
          'w-10 h-6 rounded-full transition-all duration-200 flex items-center',
          checked ? 'bg-primary-500/30' : darkMode ? 'bg-dark-600' : 'bg-light-300'
        )}>
          <div className={clsx(
            'w-4 h-4 rounded-full transition-all duration-200 shadow-sm',
            checked 
              ? `translate-x-5 ${colorClasses[iconColor].check} shadow-primary-400/50` 
              : `translate-x-1 ${darkMode ? 'bg-dark-400' : 'bg-light-400'}`
          )} />
        </div>
      </div>
      <div className="flex items-center gap-2.5 flex-1">
        {Icon && (
          <Icon size={18} className={clsx(
            'transition-colors',
            checked ? colorClasses[iconColor].icon : darkMode ? 'text-dark-400' : 'text-light-500'
          )} />
        )}
        <div>
          <div className={clsx(
            'font-medium text-sm transition-colors',
            checked 
              ? darkMode ? 'text-dark-100' : 'text-light-900'
              : darkMode ? 'text-dark-300' : 'text-light-600'
          )}>
            {label}
          </div>
          {description && (
            <div className={clsx('text-xs mt-0.5', darkMode ? 'text-dark-500' : 'text-light-500')}>{description}</div>
          )}
        </div>
      </div>
    </label>
  )
}

export default function ConfigPage() {
  const { config, setConfig, darkMode } = useStore()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('search')
  const [localConfig, setLocalConfig] = useState<Config | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    loadConfig()
  }, [])

  useEffect(() => {
    if (config) {
      setLocalConfig(JSON.parse(JSON.stringify(config)))
    }
  }, [config])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const data = await fetchConfig()
      setConfig(data)
      setLocalConfig(JSON.parse(JSON.stringify(data)))
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!localConfig) return
    
    setSaving(true)
    setSaveSuccess(false)
    try {
      await updateConfig(localConfig)
      setConfig(localConfig)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (error) {
      console.error('Failed to save config:', error)
    } finally {
      setSaving(false)
    }
  }

  const updateLocalConfig = (path: string, value: unknown) => {
    if (!localConfig) return
    
    const keys = path.split('.')
    const newConfig = { ...localConfig }
    let current: Record<string, unknown> = newConfig
    
    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = { ...(current[keys[i]] as Record<string, unknown>) }
      current = current[keys[i]] as Record<string, unknown>
    }
    
    current[keys[keys.length - 1]] = value
    setLocalConfig(newConfig)
  }

  const tabs = [
    { id: 'search', label: '搜索设置', icon: Monitor },
    { id: 'browser', label: '浏览器', icon: Globe },
    { id: 'login', label: '登录设置', icon: Key },
    { id: 'notification', label: '通知', icon: Bell },
    { id: 'scheduler', label: '调度器', icon: Clock },
    { id: 'monitoring', label: '监控', icon: Eye },
  ]

  if (loading || !localConfig) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw size={24} className="animate-spin text-primary-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">配置管理</h1>
          <p className="page-subtitle">管理应用程序的各项设置</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={loadConfig} className="btn-secondary">
            <RefreshCw size={16} />
            刷新
          </button>
          <button 
            onClick={handleSave} 
            disabled={saving} 
            className={clsx(
              'btn-primary transition-all',
              saveSuccess && 'bg-success-500 hover:bg-success-400'
            )}
          >
            {saving ? (
              <RefreshCw size={16} className="animate-spin" />
            ) : saveSuccess ? (
              <CheckCircle size={16} />
            ) : (
              <Save size={16} />
            )}
            {saveSuccess ? '已保存' : '保存配置'}
          </button>
        </div>
      </div>

      <div className="flex gap-6">
        <div className="w-48 space-y-1">
          {tabs.map((tab) => (
            <TabButton
              key={tab.id}
              {...tab}
              active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              darkMode={darkMode}
            />
          ))}
        </div>

        <div className="flex-1 card">
          {activeTab === 'search' && (
            <ConfigSection title="搜索设置" icon={Monitor}>
              <div className="grid grid-cols-2 gap-6">
                <FormField label="桌面搜索次数" hint="建议: 30 次">
                  <input
                    type="number"
                    value={localConfig.search.desktop_count}
                    onChange={(e) => updateLocalConfig('search.desktop_count', parseInt(e.target.value) || 0)}
                    className="input"
                    min="0"
                    max="100"
                  />
                </FormField>

                <FormField label="移动搜索次数" hint="建议: 20 次">
                  <input
                    type="number"
                    value={localConfig.search.mobile_count}
                    onChange={(e) => updateLocalConfig('search.mobile_count', parseInt(e.target.value) || 0)}
                    className="input"
                    min="0"
                    max="100"
                  />
                </FormField>

                <FormField label="搜索间隔 (秒)" hint="建议: 3-8 秒">
                  <input
                    type="number"
                    value={localConfig.search.wait_interval}
                    onChange={(e) => updateLocalConfig('search.wait_interval', parseInt(e.target.value) || 0)}
                    className="input"
                    min="1"
                    max="60"
                  />
                </FormField>
              </div>
            </ConfigSection>
          )}

          {activeTab === 'browser' && (
            <ConfigSection title="浏览器设置" icon={Globe} iconColor="cyan">
              <div className="space-y-4">
                <FormField label="浏览器类型">
                  <select
                    value={localConfig.browser.type}
                    onChange={(e) => updateLocalConfig('browser.type', e.target.value)}
                    className="select"
                  >
                    <option value="chromium">Chromium (推荐)</option>
                    <option value="chrome">Chrome</option>
                    <option value="edge">Edge</option>
                  </select>
                </FormField>

                <Toggle
                  label="无头模式"
                  description="不显示浏览器窗口"
                  checked={localConfig.browser.headless}
                  onChange={(checked) => updateLocalConfig('browser.headless', checked)}
                  icon={localConfig.browser.headless ? EyeOff : Eye}
                  darkMode={darkMode}
                />

                <Toggle
                  label="强制深色模式"
                  checked={localConfig.browser.force_dark_mode}
                  onChange={(checked) => updateLocalConfig('browser.force_dark_mode', checked)}
                  iconColor="neutral"
                  darkMode={darkMode}
                />
              </div>
            </ConfigSection>
          )}

          {activeTab === 'login' && (
            <ConfigSection title="登录设置" icon={Key} iconColor="warning">
              <div className="p-4 bg-warning-500/10 border border-warning-500/20 rounded-xl mb-4">
                <div className="flex items-start gap-3">
                  <AlertCircle size={18} className="text-warning-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-warning-400">
                    自动登录功能经常被微软拒绝，建议使用手动登录方式。
                  </p>
                </div>
              </div>

              <Toggle
                label="启用自动登录"
                checked={localConfig.login.auto_login.enabled}
                onChange={(checked) => updateLocalConfig('login.auto_login.enabled', checked)}
                darkMode={darkMode}
              />

              {localConfig.login.auto_login.enabled && (
                <div className={clsx('space-y-4 mt-4 p-4 rounded-xl', darkMode ? 'bg-surface-400/50' : 'bg-light-100')}>
                  <FormField label="邮箱">
                    <input
                      type="email"
                      value={localConfig.login.auto_login.email}
                      onChange={(e) => updateLocalConfig('login.auto_login.email', e.target.value)}
                      className="input"
                      placeholder="your@email.com"
                    />
                  </FormField>

                  <FormField label="密码">
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={localConfig.login.auto_login.password}
                        onChange={(e) => updateLocalConfig('login.auto_login.password', e.target.value)}
                        className="input pr-10"
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-100 transition-colors"
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </FormField>

                  <FormField label="TOTP 密钥 (2FA)" hint="可选，用于双因素认证">
                    <input
                      type="password"
                      value={localConfig.login.auto_login.totp_secret}
                      onChange={(e) => updateLocalConfig('login.auto_login.totp_secret', e.target.value)}
                      className="input"
                      placeholder="从验证器应用获取"
                    />
                  </FormField>
                </div>
              )}
            </ConfigSection>
          )}

          {activeTab === 'notification' && (
            <ConfigSection title="通知设置" icon={Bell} iconColor="success">
              <Toggle
                label="启用通知"
                checked={localConfig.notification.enabled}
                onChange={(checked) => updateLocalConfig('notification.enabled', checked)}
                darkMode={darkMode}
              />

              {localConfig.notification.enabled && (
                <div className={clsx('space-y-4 mt-4 p-4 rounded-xl', darkMode ? 'bg-surface-400/50' : 'bg-light-100')}>
                  <h3 className={clsx('font-medium flex items-center gap-2', darkMode ? 'text-dark-100' : 'text-light-900')}>
                    <Shield size={16} className="text-primary-400" />
                    Telegram 配置
                  </h3>
                  <div className="space-y-4">
                    <FormField label="Bot Token">
                      <input
                        type="password"
                        value={localConfig.notification.telegram.bot_token}
                        onChange={(e) => updateLocalConfig('notification.telegram.bot_token', e.target.value)}
                        className="input"
                        placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                      />
                    </FormField>
                    <FormField label="Chat ID">
                      <input
                        type="text"
                        value={localConfig.notification.telegram.chat_id}
                        onChange={(e) => updateLocalConfig('notification.telegram.chat_id', e.target.value)}
                        className="input"
                        placeholder="123456789"
                      />
                    </FormField>
                  </div>
                </div>
              )}
            </ConfigSection>
          )}

          {activeTab === 'scheduler' && (
            <ConfigSection title="调度器设置" icon={Clock} iconColor="cyan">
              <Toggle
                label="启用调度器"
                checked={localConfig.scheduler.enabled}
                onChange={(checked) => updateLocalConfig('scheduler.enabled', checked)}
                darkMode={darkMode}
              />

              {localConfig.scheduler.enabled && (
                <div className="space-y-4 mt-4">
                  <FormField label="调度模式">
                    <select
                      value={localConfig.scheduler.mode}
                      onChange={(e) => updateLocalConfig('scheduler.mode', e.target.value)}
                      className="select"
                    >
                      <option value="random">随机时间</option>
                      <option value="fixed">固定时间</option>
                    </select>
                  </FormField>

                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="开始时间 (小时)">
                      <input
                        type="number"
                        value={localConfig.scheduler.random_start_hour}
                        onChange={(e) => updateLocalConfig('scheduler.random_start_hour', parseInt(e.target.value) || 0)}
                        className="input"
                        min="0"
                        max="23"
                      />
                    </FormField>
                    <FormField label="结束时间 (小时)">
                      <input
                        type="number"
                        value={localConfig.scheduler.random_end_hour}
                        onChange={(e) => updateLocalConfig('scheduler.random_end_hour', parseInt(e.target.value) || 0)}
                        className="input"
                        min="0"
                        max="23"
                      />
                    </FormField>
                  </div>
                </div>
              )}
            </ConfigSection>
          )}

          {activeTab === 'monitoring' && (
            <ConfigSection title="监控设置" icon={Eye}>
              <div className="space-y-4">
                <Toggle
                  label="启用健康监控"
                  checked={localConfig.monitoring.health_check.enabled}
                  onChange={(checked) => updateLocalConfig('monitoring.health_check.enabled', checked)}
                  darkMode={darkMode}
                />

                {localConfig.monitoring.health_check.enabled && (
                  <FormField label="检查间隔 (秒)">
                    <input
                      type="number"
                      value={localConfig.monitoring.health_check.interval}
                      onChange={(e) => updateLocalConfig('monitoring.health_check.interval', parseInt(e.target.value) || 30)}
                      className="input"
                      min="10"
                      max="300"
                    />
                  </FormField>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <Toggle
                    label="启用任务系统"
                    checked={localConfig.task_system.enabled}
                    onChange={(checked) => updateLocalConfig('task_system.enabled', checked)}
                    darkMode={darkMode}
                  />
                  <Toggle
                    label="启用主题管理"
                    checked={localConfig.bing_theme.enabled}
                    onChange={(checked) => updateLocalConfig('bing_theme.enabled', checked)}
                    darkMode={darkMode}
                  />
                </div>
              </div>
            </ConfigSection>
          )}
        </div>
      </div>
    </div>
  )
}
