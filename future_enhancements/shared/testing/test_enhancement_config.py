"""
Test cases for enhancement configuration and feature flags
"""

import pytest
import os
from future_enhancements.shared.config.enhancement_config import (
    FeatureFlags, 
    EnhancementConfig, 
    is_feature_enabled
)


class TestFeatureFlags:
    """Test feature flag functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.feature_flags = FeatureFlags()
    
    def test_default_flags_disabled(self):
        """Test that all flags are disabled by default"""
        assert not self.feature_flags.is_enabled('analytics_enabled')
        assert not self.feature_flags.is_enabled('ml_forecasting')
        assert not self.feature_flags.is_enabled('custom_dashboards')
        assert not self.feature_flags.is_enabled('chatbot_enabled')
    
    def test_enable_feature_flag(self):
        """Test enabling a feature flag"""
        self.feature_flags.set_flag('analytics_enabled', True)
        assert self.feature_flags.is_enabled('analytics_enabled')
    
    def test_disable_feature_flag(self):
        """Test disabling a feature flag"""
        self.feature_flags.set_flag('analytics_enabled', True)
        self.feature_flags.set_flag('analytics_enabled', False)
        assert not self.feature_flags.is_enabled('analytics_enabled')
    
    def test_nonexistent_flag(self):
        """Test checking a nonexistent flag returns False"""
        assert not self.feature_flags.is_enabled('nonexistent_flag')
    
    def test_get_all_flags(self):
        """Test getting all feature flags"""
        flags = self.feature_flags.get_all_flags()
        assert isinstance(flags, dict)
        assert 'analytics_enabled' in flags
        assert 'chatbot_enabled' in flags


class TestEnhancementConfig:
    """Test enhancement configuration"""
    
    def setup_method(self):
        """Set up test environment"""
        self.config = EnhancementConfig()
    
    def test_environment_detection(self):
        """Test environment detection"""
        assert self.config.environment in ['development', 'testing', 'production']
    
    def test_analytics_config(self):
        """Test analytics configuration"""
        analytics_config = self.config.analytics_config
        assert isinstance(analytics_config, dict)
        assert 'celery_broker_url' in analytics_config
        assert 'report_storage_path' in analytics_config
    
    def test_mobile_config(self):
        """Test mobile configuration"""
        mobile_config = self.config.mobile_config
        assert isinstance(mobile_config, dict)
        assert 'push_notifications_key' in mobile_config
    
    def test_ai_config(self):
        """Test AI configuration"""
        ai_config = self.config.ai_config
        assert isinstance(ai_config, dict)
        assert 'openai_api_key' in ai_config
        assert 'model_storage_path' in ai_config
    
    def test_integration_config(self):
        """Test integration configuration"""
        integration_config = self.config.integration_config
        assert isinstance(integration_config, dict)
        assert 'quickbooks_client_id' in integration_config


class TestGlobalFunctions:
    """Test global configuration functions"""
    
    def test_is_feature_enabled_function(self):
        """Test global is_feature_enabled function"""
        # Should return False by default
        assert not is_feature_enabled('analytics_enabled')
        assert not is_feature_enabled('nonexistent_flag')
    
    def test_feature_flag_environment_override(self):
        """Test that environment variables can override feature flags"""
        # Temporarily set environment variable
        os.environ['ANALYTICS_ENABLED'] = 'true'
        
        # Create new config to pick up environment change
        config = EnhancementConfig()
        assert config.feature_flags.is_enabled('analytics_enabled')
        
        # Clean up
        del os.environ['ANALYTICS_ENABLED']


if __name__ == '__main__':
    pytest.main([__file__])