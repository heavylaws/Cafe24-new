"""
Shared configuration management for Cafe24 enhancements
"""

import os
from typing import Dict, Any, Optional


class FeatureFlags:
    """Feature flag management for gradual rollout of enhancements"""
    
    def __init__(self):
        self.flags = {
            # Phase 1: Analytics & Reporting
            'analytics_enabled': self._get_bool_env('ANALYTICS_ENABLED', False),
            'ml_forecasting': self._get_bool_env('ML_FORECASTING', False),
            'custom_dashboards': self._get_bool_env('CUSTOM_DASHBOARDS', False),
            'automated_reports': self._get_bool_env('AUTOMATED_REPORTS', False),
            
            # Phase 2: Mobile & Omnichannel
            'pwa_offline': self._get_bool_env('PWA_OFFLINE', False),
            'mobile_payments': self._get_bool_env('MOBILE_PAYMENTS', False),
            'qr_ordering': self._get_bool_env('QR_ORDERING', False),
            'social_ordering': self._get_bool_env('SOCIAL_ORDERING', False),
            
            # Phase 3: AI & Automation
            'chatbot_enabled': self._get_bool_env('CHATBOT_ENABLED', False),
            'ai_recommendations': self._get_bool_env('AI_RECOMMENDATIONS', False),
            'auto_inventory': self._get_bool_env('AUTO_INVENTORY', False),
            'dynamic_pricing': self._get_bool_env('DYNAMIC_PRICING', False),
            
            # Phase 4: Advanced Integrations
            'accounting_sync': self._get_bool_env('ACCOUNTING_SYNC', False),
            'crm_integration': self._get_bool_env('CRM_INTEGRATION', False),
            'public_api': self._get_bool_env('PUBLIC_API', False),
            'webhook_system': self._get_bool_env('WEBHOOK_SYSTEM', False),
            
            # Research & Innovation
            'blockchain_tracking': self._get_bool_env('BLOCKCHAIN_TRACKING', False),
            'iot_monitoring': self._get_bool_env('IOT_MONITORING', False),
            'ar_menu': self._get_bool_env('AR_MENU', False),
            'biometric_auth': self._get_bool_env('BIOMETRIC_AUTH', False),
        }
    
    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.flags.get(feature, False)
    
    def set_flag(self, feature: str, enabled: bool) -> None:
        """Set a feature flag (for testing purposes)"""
        self.flags[feature] = enabled
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.flags.copy()


class EnhancementConfig:
    """Configuration for enhancement phases"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.feature_flags = FeatureFlags()
        
        # Phase-specific configurations
        self.analytics_config = self._get_analytics_config()
        self.mobile_config = self._get_mobile_config()
        self.ai_config = self._get_ai_config()
        self.integration_config = self._get_integration_config()
    
    def _get_analytics_config(self) -> Dict[str, Any]:
        """Analytics phase configuration"""
        return {
            'celery_broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379'),
            'report_storage_path': os.getenv('REPORT_STORAGE_PATH', '/tmp/reports'),
            'ml_model_path': os.getenv('ML_MODEL_PATH', '/tmp/models'),
            'analytics_db_url': os.getenv('ANALYTICS_DB_URL', ''),
        }
    
    def _get_mobile_config(self) -> Dict[str, Any]:
        """Mobile phase configuration"""
        return {
            'push_notifications_key': os.getenv('PUSH_NOTIFICATIONS_KEY', ''),
            'stripe_publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY', ''),
            'apple_pay_merchant_id': os.getenv('APPLE_PAY_MERCHANT_ID', ''),
            'google_pay_merchant_id': os.getenv('GOOGLE_PAY_MERCHANT_ID', ''),
            'whatsapp_api_token': os.getenv('WHATSAPP_API_TOKEN', ''),
        }
    
    def _get_ai_config(self) -> Dict[str, Any]:
        """AI phase configuration"""
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'model_storage_path': os.getenv('MODEL_STORAGE_PATH', '/tmp/ai_models'),
            'gpu_enabled': os.getenv('CUDA_VISIBLE_DEVICES', '') != '',
            'tensorflow_gpu_memory_growth': os.getenv('TF_GPU_MEMORY_GROWTH', 'true'),
        }
    
    def _get_integration_config(self) -> Dict[str, Any]:
        """Integration phase configuration"""
        return {
            'quickbooks_client_id': os.getenv('QUICKBOOKS_CLIENT_ID', ''),
            'quickbooks_client_secret': os.getenv('QUICKBOOKS_CLIENT_SECRET', ''),
            'xero_client_id': os.getenv('XERO_CLIENT_ID', ''),
            'xero_client_secret': os.getenv('XERO_CLIENT_SECRET', ''),
            'salesforce_client_id': os.getenv('SALESFORCE_CLIENT_ID', ''),
            'hubspot_api_key': os.getenv('HUBSPOT_API_KEY', ''),
            'webhook_secret_key': os.getenv('WEBHOOK_SECRET_KEY', ''),
        }


# Global configuration instance
enhancement_config = EnhancementConfig()


def is_feature_enabled(feature: str) -> bool:
    """Convenience function to check feature flags"""
    return enhancement_config.feature_flags.is_enabled(feature)


def get_config(phase: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific phase"""
    config_map = {
        'analytics': enhancement_config.analytics_config,
        'mobile': enhancement_config.mobile_config,
        'ai': enhancement_config.ai_config,
        'integration': enhancement_config.integration_config,
    }
    return config_map.get(phase)