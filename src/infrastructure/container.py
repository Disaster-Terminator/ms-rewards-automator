"""
Dependency Injection Container - 依赖注入容器

提供简单的依赖注入功能，降低组件间的耦合度。
支持：
- 注册服务（单例或瞬态）
- 自动解析依赖
- 工厂方法注册
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")


class ServiceNotFoundError(Exception):
    """服务未找到异常"""

    pass


class CyclicDependencyError(Exception):
    """循环依赖异常"""

    pass


class Container:
    """
    简单的依赖注入容器

    支持:
    - 单例模式 (singleton)
    - 瞬态模式 (transient)
    - 工厂模式 (factory)
    """

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}
        self._types: dict[str, type] = {}
        self._lifetimes: dict[str, str] = {}  # singleton, transient, factory

    def register_singleton(
        self,
        service_type: type[T],
        instance: T | None = None,
        factory: Callable[..., T] | None = None,
    ) -> "Container":
        """
        注册单例服务

        Args:
            service_type: 服务类型
            instance: 实例（可选）
            factory: 工厂函数（可选）

        Returns:
            Self (支持链式调用)
        """
        type_name = self._get_type_name(service_type)
        self._types[type_name] = service_type
        self._lifetimes[type_name] = "singleton"

        if instance is not None:
            self._services[type_name] = instance
        elif factory is not None:
            self._factories[type_name] = factory
        else:
            # 使用类型本身作为工厂
            self._factories[type_name] = lambda: service_type()

        return self

    def register_transient(
        self, service_type: type[T], factory: Callable[..., T] | None = None
    ) -> "Container":
        """
        注册瞬态服务（每次请求创建新实例）

        Args:
            service_type: 服务类型
            factory: 工厂函数（可选）

        Returns:
            Self (支持链式调用)
        """
        type_name = self._get_type_name(service_type)
        self._types[type_name] = service_type
        self._lifetimes[type_name] = "transient"

        if factory is not None:
            self._factories[type_name] = factory
        else:
            self._factories[type_name] = lambda: service_type()

        return self

    def register_factory(self, service_type: type[T], factory: Callable[..., T]) -> "Container":
        """
        注册工厂服务

        Args:
            service_type: 服务类型
            factory: 工厂函数

        Returns:
            Self (支持链式调用)
        """
        type_name = self._get_type_name(service_type)
        self._types[type_name] = service_type
        self._lifetimes[type_name] = "factory"
        self._factories[type_name] = factory

        return self

    def register_instance(self, service_type: type[T], instance: T) -> "Container":
        """
        注册实例（快捷方式，等同于 register_singleton with instance）

        Args:
            service_type: 服务类型
            instance: 实例

        Returns:
            Self (支持链式调用)
        """
        return self.register_singleton(service_type, instance=instance)

    def resolve(self, service_type: type[T]) -> T:
        """
        解析服务

        Args:
            service_type: 服务类型

        Returns:
            服务实例

        Raises:
            ServiceNotFoundError: 服务未注册
        """
        type_name = self._get_type_name(service_type)

        if type_name not in self._factories:
            raise ServiceNotFoundError(f"服务 {service_type} 未注册")

        lifetime = self._lifetimes.get(type_name, "transient")

        if lifetime == "singleton" and type_name in self._services:
            return self._services[type_name]

        # 创建实例
        factory = self._factories[type_name]
        instance = self._create_instance(factory, type_name)

        if lifetime == "singleton":
            self._services[type_name] = instance

        return instance

    def resolve_by_name(self, service_name: str) -> Any:
        """
        通过名称解析服务

        Args:
            service_name: 服务名称

        Returns:
            服务实例
        """
        if service_name not in self._factories:
            raise ServiceNotFoundError(f"服务 {service_name} 未注册")

        lifetime = self._lifetimes.get(service_name, "transient")

        if lifetime == "singleton" and service_name in self._services:
            return self._services[service_name]

        factory = self._factories[service_name]
        instance = self._create_instance(factory, service_name)

        if lifetime == "singleton":
            self._services[service_name] = instance

        return instance

    def _create_instance(self, factory: Callable, type_name: str) -> Any:
        """创建实例并解析依赖"""
        # 检查是否是带依赖的函数
        try:
            sig = inspect.signature(factory)
            params = sig.parameters

            # 如果工厂函数没有参数，直接调用
            if not params:
                return factory()

            # 解析依赖
            dependencies = {}
            for param_name, param in params.items():
                param_type = param.annotation
                if param_type is inspect.Parameter.empty:
                    # 尝试通过参数名推断
                    param_type = self._types.get(param_name)

                if param_type:
                    try:
                        dependencies[param_name] = self.resolve(param_type)
                    except ServiceNotFoundError:
                        # 使用默认值（如果提供）
                        if param.default is not inspect.Parameter.empty:
                            dependencies[param_name] = param.default
                        else:
                            raise

            return factory(**dependencies)

        except CyclicDependencyError:
            raise
        except Exception:
            # 如果是单例且已存在，返回现有实例
            if type_name in self._services:
                return self._services[type_name]
            raise

    def _get_type_name(self, service_type: type) -> str:
        """获取类型名称"""
        if isinstance(service_type, str):
            return service_type
        return service_type.__name__

    def clear(self) -> None:
        """清除所有注册的服务"""
        self._services.clear()
        self._factories.clear()
        self._types.clear()
        self._lifetimes.clear()

    def is_registered(self, service_type: type) -> bool:
        """检查服务是否已注册"""
        type_name = self._get_type_name(service_type)
        return type_name in self._factories


# ============================================================
# 依赖注入装饰器
# ============================================================

_injector_container: Container | None = None


def set_container(container: Container) -> None:
    """设置全局容器"""
    global _injector_container
    _injector_container = container


def get_container() -> Container:
    """获取全局容器"""
    global _injector_container
    if _injector_container is None:
        _injector_container = Container()
    return _injector_container


def injectable(func_or_cls: Any = None, lifetime: str = "singleton") -> Any:
    """
    可注入装饰器

    用法:
    @injectable()
    class MyService:
        pass

    @injectable()
    def my_factory(config: Config) -> MyService:
        return MyService(config)
    """

    def decorator(cls_or_func):
        container = get_container()
        service_type = cls_or_func.__name__

        if inspect.isclass(cls_or_func):
            if lifetime == "singleton":
                container.register_singleton(cls_or_func)
            else:
                container.register_transient(cls_or_func)
        else:
            # 工厂函数
            container.register_factory(service_type, cls_or_func)

        return cls_or_func

    # 处理无参数调用
    if callable(func_or_cls):
        return decorator(func_or_cls)
    return decorator


def inject(**dependencies: type) -> Callable:
    """
    注入依赖装饰器

    用法:
    @inject(config=Config, logger=Logger)
    class MyService:
        def __init__(self, config, logger):
            self.config = config
            self.logger = logger
    """

    def decorator(cls):
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            container = get_container()

            # 解析依赖
            for dep_name, dep_type in dependencies.items():
                if dep_name not in kwargs:
                    try:
                        kwargs[dep_name] = container.resolve(dep_type)
                    except ServiceNotFoundError:
                        pass  # 使用默认值或忽略

            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator


# ============================================================
# 便捷函数
# ============================================================


def register_services(container: Container, config: Any) -> Container:
    """
    注册所有核心服务

    Args:
        container: 容器实例
        config: 配置对象

    Returns:
        已注册的容器
    """
    from account.manager import AccountManager
    from account.points_detector import PointsDetector
    from browser.anti_ban_module import AntiBanModule
    from browser.simulator import BrowserSimulator
    from infrastructure.error_handler import ErrorHandler
    from infrastructure.health_monitor import HealthMonitor
    from infrastructure.notificator import Notificator
    from infrastructure.state_monitor import StateMonitor
    from search.search_engine import SearchEngine
    from search.search_term_generator import SearchTermGenerator
    from tasks import TaskManager

    # 注册配置
    container.register_instance("Config", config)

    # 注册单例服务
    container.register_singleton(AntiBanModule, lambda c: AntiBanModule(c))
    container.register_singleton(
        BrowserSimulator, lambda c: BrowserSimulator(c, c.resolve(AntiBanModule))
    )
    container.register_singleton(SearchTermGenerator, lambda c: SearchTermGenerator(c))
    container.register_singleton(PointsDetector)
    container.register_singleton(StateMonitor, lambda c: StateMonitor(c, c.resolve(PointsDetector)))
    container.register_singleton(ErrorHandler, lambda c: ErrorHandler(c))
    container.register_singleton(Notificator, lambda c: Notificator(c))
    container.register_singleton(HealthMonitor, lambda c: HealthMonitor(c))

    # 注册瞬态服务
    container.register_transient(SearchEngine)
    container.register_transient(AccountManager)
    container.register_transient(TaskManager)

    return container
