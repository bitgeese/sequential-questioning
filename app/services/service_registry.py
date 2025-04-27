from typing import Dict, Any, Type
import logging

class ServiceRegistry:
    """Registry for maintaining service references."""
    
    _services = {}
    
    @classmethod
    def register(cls, service_name: str, service_instance: Any) -> None:
        """Register a service instance.
        
        Args:
            service_name: Name of the service
            service_instance: Instance of the service
        """
        cls._services[service_name] = service_instance
    
    @classmethod
    def get(cls, service_name: str) -> Any:
        """Get a service instance by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service instance
        
        Raises:
            KeyError: If service is not registered
        """
        if service_name not in cls._services:
            raise KeyError(f"Service '{service_name}' not registered")
        return cls._services[service_name]
    
    @classmethod
    def is_registered(cls, service_name: str) -> bool:
        """Check if a service is registered.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if service is registered, False otherwise
        """
        return service_name in cls._services 