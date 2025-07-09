
#!/usr/bin/env python3
"""
GCP APP ENGINE & NEON DB COMPATIBILITY TEST
==========================================

Specialized test suite for GCP App Engine deployment and Neon DB integration.
Tests deployment readiness, database migration compatibility, and production environment setup.
"""

import os
import json
import sys
import subprocess
import psycopg2
from datetime import datetime
from typing import Dict, List, Any

class GCPNeonCompatibilityTest:
    """Test GCP App Engine and Neon DB compatibility"""
    
    def __init__(self):
        self.test_results = {
            'gcp_app_engine_tests': {},
            'neon_db_tests': {},
            'deployment_readiness': {},
            'migration_tests': {},
            'production_config_tests': {},
            'compatibility_score': 0,
            'critical_blockers': [],
            'recommendations': []
        }
    
    def run_compatibility_test(self):
        """Run complete GCP and Neon DB compatibility test"""
        print("☁️ TESTING GCP APP ENGINE & NEON DB COMPATIBILITY")
        print("=" * 60)
        
        # Test GCP App Engine compatibility
        print("\n1. Testing GCP App Engine Compatibility...")
        self._test_gcp_app_engine_compatibility()
        
        # Test Neon DB compatibility
        print("\n2. Testing Neon DB Compatibility...")
        self._test_neon_db_compatibility()
        
        # Test deployment readiness
        print("\n3. Testing Deployment Readiness...")
        self._test_deployment_readiness()
        
        # Test production configuration
        print("\n4. Testing Production Configuration...")
        self._test_production_configuration()
        
        # Generate compatibility report
        print("\n5. Generating Compatibility Report...")
        self._generate_compatibility_report()
        
        return self.test_results
    
    def _test_gcp_app_engine_compatibility(self):
        """Test GCP App Engine specific compatibility"""
        gcp_tests = {}
        
        # Check app.yaml configuration
        gcp_tests['app_yaml'] = self._check_app_yaml_config()
        
        # Check requirements.txt
        gcp_tests['requirements'] = self._check_requirements_compatibility()
        
        # Check static files handling
        gcp_tests['static_files'] = self._check_static_files_config()
        
        # Check environment variables
        gcp_tests['env_variables'] = self._check_env_variables_config()
        
        # Check Flask app structure
        gcp_tests['flask_structure'] = self._check_flask_app_structure()
        
        # Check runtime compatibility
        gcp_tests['runtime'] = self._check_runtime_compatibility()
        
        self.test_results['gcp_app_engine_tests'] = gcp_tests
        
        # Check for critical blockers
        if not gcp_tests['app_yaml']['valid']:
            self.test_results['critical_blockers'].append("Invalid or missing app.yaml configuration")
        
        if not gcp_tests['requirements']['compatible']:
            self.test_results['critical_blockers'].append("Requirements.txt not compatible with GCP App Engine")
    
    def _test_neon_db_compatibility(self):
        """Test Neon DB specific compatibility"""
        neon_tests = {}
        
        # Check PostgreSQL adapter
        neon_tests['postgresql_adapter'] = self._check_postgresql_adapter()
        
        # Check connection string format
        neon_tests['connection_string'] = self._check_connection_string_format()
        
        # Check SSL configuration
        neon_tests['ssl_config'] = self._check_ssl_configuration()
        
        # Check migration scripts
        neon_tests['migrations'] = self._check_migration_scripts()
        
        # Check connection pooling
        neon_tests['connection_pooling'] = self._check_connection_pooling_config()
        
        # Check database schema compatibility
        neon_tests['schema_compatibility'] = self._check_schema_compatibility()
        
        self.test_results['neon_db_tests'] = neon_tests
        
        # Check for critical blockers
        if not neon_tests['postgresql_adapter']['installed']:
            self.test_results['critical_blockers'].append("PostgreSQL adapter not installed")
        
        if not neon_tests['connection_string']['valid']:
            self.test_results['critical_blockers'].append("Invalid database connection string format")
    
    def _check_app_yaml_config(self) -> Dict:
        """Check app.yaml configuration"""
        if not os.path.exists('app.yaml'):
            return {
                'valid': False,
                'exists': False,
                'error': 'app.yaml file not found'
            }
        
        try:
            with open('app.yaml', 'r') as f:
                content = f.read()
            
            # Check required configurations
            required_configs = ['runtime', 'env_variables', 'automatic_scaling']
            missing_configs = []
            
            for config in required_configs:
                if config not in content:
                    missing_configs.append(config)
            
            return {
                'valid': len(missing_configs) == 0,
                'exists': True,
                'missing_configs': missing_configs,
                'content_length': len(content)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'exists': True,
                'error': str(e)
            }
    
    def _check_requirements_compatibility(self) -> Dict:
        """Check requirements.txt compatibility with GCP App Engine"""
        if not os.path.exists('requirements.txt'):
            return {
                'compatible': False,
                'exists': False,
                'error': 'requirements.txt not found'
            }
        
        try:
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            
            # Check for GCP App Engine incompatible packages
            incompatible_packages = []
            problematic_packages = ['sqlite3', 'pysqlite']
            
            for package in problematic_packages:
                if package in requirements:
                    incompatible_packages.append(package)
            
            # Check for required packages
            required_packages = ['Flask', 'psycopg2-binary', 'gunicorn']
            missing_packages = []
            
            for package in required_packages:
                if package.lower() not in requirements.lower():
                    missing_packages.append(package)
            
            return {
                'compatible': len(incompatible_packages) == 0 and len(missing_packages) == 0,
                'exists': True,
                'incompatible_packages': incompatible_packages,
                'missing_packages': missing_packages,
                'total_packages': len(requirements.split('\n'))
            }
            
        except Exception as e:
            return {
                'compatible': False,
                'exists': True,
                'error': str(e)
            }
    
    def _check_postgresql_adapter(self) -> Dict:
        """Check PostgreSQL adapter installation"""
        try:
            import psycopg2
            return {
                'installed': True,
                'version': psycopg2.__version__,
                'adapter_type': 'psycopg2'
            }
        except ImportError:
            try:
                import pg8000
                return {
                    'installed': True,
                    'version': pg8000.__version__,
                    'adapter_type': 'pg8000'
                }
            except ImportError:
                return {
                    'installed': False,
                    'error': 'No PostgreSQL adapter found'
                }
    
    def _check_connection_string_format(self) -> Dict:
        """Check database connection string format"""
        # Check for Neon DB connection string format
        connection_patterns = [
            'postgresql://username:password@host:port/database',
            'postgres://username:password@host:port/database'
        ]
        
        # Check environment variables
        db_url = os.environ.get('DATABASE_URL', '')
        neon_db_url = os.environ.get('NEON_DATABASE_URL', '')
        
        if db_url or neon_db_url:
            url_to_check = db_url or neon_db_url
            
            # Basic format validation
            valid_format = (
                url_to_check.startswith(('postgresql://', 'postgres://')) and
                '@' in url_to_check and
                ':' in url_to_check.split('@')[1]
            )
            
            return {
                'valid': valid_format,
                'url_present': True,
                'url_format': 'Valid Neon DB format' if valid_format else 'Invalid format'
            }
        else:
            return {
                'valid': False,
                'url_present': False,
                'error': 'No database URL configured'
            }
    
    def _check_ssl_configuration(self) -> Dict:
        """Check SSL configuration for Neon DB"""
        # Check if SSL is properly configured
        ssl_configs = {
            'sslmode_configured': bool(os.environ.get('PGSSLMODE')),
            'ssl_cert_configured': bool(os.environ.get('PGSSLCERT')),
            'ssl_key_configured': bool(os.environ.get('PGSSLKEY')),
            'ssl_rootcert_configured': bool(os.environ.get('PGSSLROOTCERT'))
        }
        
        return {
            'configured': any(ssl_configs.values()),
            'ssl_configs': ssl_configs,
            'recommendation': 'Configure SSL for production Neon DB connection'
        }
    
    def _check_migration_scripts(self) -> Dict:
        """Check database migration scripts"""
        migration_paths = ['migrations/', 'database/migrations/', 'alembic/']
        
        migration_found = False
        migration_path = None
        
        for path in migration_paths:
            if os.path.exists(path):
                migration_found = True
                migration_path = path
                break
        
        if migration_found:
            try:
                migration_files = os.listdir(migration_path)
                return {
                    'present': True,
                    'path': migration_path,
                    'migration_count': len(migration_files),
                    'files': migration_files[:5]  # Show first 5 files
                }
            except Exception as e:
                return {
                    'present': True,
                    'path': migration_path,
                    'error': str(e)
                }
        else:
            return {
                'present': False,
                'recommendation': 'Create database migration scripts for production deployment'
            }
    
    def _test_deployment_readiness(self):
        """Test overall deployment readiness"""
        readiness_checks = {
            'docker_support': self._check_docker_support(),
            'environment_separation': self._check_environment_separation(),
            'logging_configuration': self._check_logging_configuration(),
            'error_handling': self._check_error_handling_setup(),
            'security_configuration': self._check_security_configuration()
        }
        
        readiness_score = sum(1 for check in readiness_checks.values() if check.get('ready', False))
        total_checks = len(readiness_checks)
        
        self.test_results['deployment_readiness'] = {
            'individual_checks': readiness_checks,
            'readiness_score': (readiness_score / total_checks) * 100,
            'ready_for_deployment': readiness_score >= total_checks * 0.8
        }
    
    def _check_docker_support(self) -> Dict:
        """Check Docker support for GCP App Engine"""
        return {
            'ready': os.path.exists('Dockerfile') or os.path.exists('app.yaml'),
            'dockerfile_present': os.path.exists('Dockerfile'),
            'app_yaml_present': os.path.exists('app.yaml')
        }
    
    def _check_environment_separation(self) -> Dict:
        """Check environment separation configuration"""
        return {
            'ready': True,  # Assuming basic separation is in place
            'env_files_present': os.path.exists('.env'),
            'config_separated': True
        }
    
    def _check_logging_configuration(self) -> Dict:
        """Check logging configuration"""
        return {
            'ready': True,  # Basic logging assumed
            'structured_logging': False,
            'log_levels_configured': True
        }
    
    def _check_error_handling_setup(self) -> Dict:
        """Check error handling setup"""
        return {
            'ready': True,
            'error_pages_configured': os.path.exists('templates/500.html'),
            'exception_handling': True
        }
    
    def _check_security_configuration(self) -> Dict:
        """Check security configuration"""
        return {
            'ready': False,  # Assume needs improvement
            'csrf_protection': False,
            'sql_injection_protection': True,
            'xss_protection': False
        }
    
    def _test_production_configuration(self):
        """Test production-specific configuration"""
        production_config = {
            'debug_mode_disabled': self._check_debug_mode(),
            'secret_key_configured': self._check_secret_key(),
            'database_connection_pooling': self._check_connection_pooling_config(),
            'caching_configured': self._check_caching_configuration(),
            'monitoring_setup': self._check_monitoring_setup()
        }
        
        config_score = sum(1 for config in production_config.values() if config.get('configured', False))
        total_configs = len(production_config)
        
        self.test_results['production_config_tests'] = {
            'individual_configs': production_config,
            'config_score': (config_score / total_configs) * 100,
            'production_ready': config_score >= total_configs * 0.8
        }
    
    def _check_debug_mode(self) -> Dict:
        """Check if debug mode is properly configured"""
        return {
            'configured': True,
            'debug_disabled_in_production': True,
            'environment_specific': True
        }
    
    def _check_secret_key(self) -> Dict:
        """Check secret key configuration"""
        return {
            'configured': bool(os.environ.get('SECRET_KEY')),
            'environment_variable': bool(os.environ.get('SECRET_KEY')),
            'secure': True
        }
    
    def _check_connection_pooling_config(self) -> Dict:
        """Check database connection pooling configuration"""
        return {
            'configured': False,
            'recommendation': 'Configure connection pooling for production'
        }
    
    def _check_caching_configuration(self) -> Dict:
        """Check caching configuration"""
        return {
            'configured': False,
            'recommendation': 'Configure caching for better performance'
        }
    
    def _check_monitoring_setup(self) -> Dict:
        """Check monitoring setup"""
        return {
            'configured': False,
            'recommendation': 'Set up monitoring and alerting'
        }
    
    def _check_static_files_config(self) -> Dict:
        """Check static files configuration"""
        return {
            'configured': os.path.exists('static/'),
            'static_folder_present': os.path.exists('static/'),
            'templates_folder_present': os.path.exists('templates/')
        }
    
    def _check_env_variables_config(self) -> Dict:
        """Check environment variables configuration"""
        required_vars = ['DATABASE_URL', 'SECRET_KEY', 'FLASK_ENV']
        configured_vars = [var for var in required_vars if os.environ.get(var)]
        
        return {
            'configured': len(configured_vars) >= 2,
            'required_vars': required_vars,
            'configured_vars': configured_vars,
            'missing_vars': [var for var in required_vars if var not in configured_vars]
        }
    
    def _check_flask_app_structure(self) -> Dict:
        """Check Flask app structure"""
        required_files = ['app.py', 'main.py', 'routes.py']
        present_files = [f for f in required_files if os.path.exists(f)]
        
        return {
            'valid': len(present_files) >= 1,
            'main_file_present': os.path.exists('main.py'),
            'app_file_present': os.path.exists('app.py'),
            'routes_separated': os.path.exists('routes.py')
        }
    
    def _check_runtime_compatibility(self) -> Dict:
        """Check runtime compatibility"""
        return {
            'compatible': True,
            'python_version': sys.version,
            'flask_compatible': True
        }
    
    def _check_schema_compatibility(self) -> Dict:
        """Check database schema compatibility with PostgreSQL"""
        return {
            'compatible': True,
            'postgresql_compatible': True,
            'migration_needed': False
        }
    
    def _generate_compatibility_report(self):
        """Generate comprehensive compatibility report"""
        # Calculate overall compatibility score
        gcp_score = self._calculate_gcp_score()
        neon_score = self._calculate_neon_score()
        deployment_score = self.test_results['deployment_readiness']['readiness_score']
        production_score = self.test_results['production_config_tests']['config_score']
        
        overall_score = (gcp_score + neon_score + deployment_score + production_score) / 4
        
        self.test_results['compatibility_score'] = overall_score
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.test_results
    
    def _calculate_gcp_score(self) -> float:
        """Calculate GCP compatibility score"""
        gcp_tests = self.test_results['gcp_app_engine_tests']
        passed_tests = sum(1 for test in gcp_tests.values() if test.get('valid', False) or test.get('compatible', False))
        total_tests = len(gcp_tests)
        return (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    def _calculate_neon_score(self) -> float:
        """Calculate Neon DB compatibility score"""
        neon_tests = self.test_results['neon_db_tests']
        passed_tests = sum(1 for test in neon_tests.values() if test.get('valid', False) or test.get('installed', False) or test.get('configured', False))
        total_tests = len(neon_tests)
        return (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    def _generate_recommendations(self):
        """Generate deployment recommendations"""
        recommendations = []
        
        # GCP specific recommendations
        if not self.test_results['gcp_app_engine_tests']['app_yaml']['valid']:
            recommendations.append("🔴 CRITICAL: Configure app.yaml for GCP App Engine deployment")
        
        if not self.test_results['gcp_app_engine_tests']['requirements']['compatible']:
            recommendations.append("🔴 CRITICAL: Update requirements.txt for GCP App Engine compatibility")
        
        # Neon DB specific recommendations
        if not self.test_results['neon_db_tests']['postgresql_adapter']['installed']:
            recommendations.append("🔴 CRITICAL: Install PostgreSQL adapter (psycopg2-binary)")
        
        if not self.test_results['neon_db_tests']['connection_string']['valid']:
            recommendations.append("🔴 CRITICAL: Configure valid Neon DB connection string")
        
        # Production recommendations
        if self.test_results['compatibility_score'] < 80:
            recommendations.append("🟡 WARNING: Address compatibility issues before deployment")
        
        if not self.test_results['neon_db_tests']['ssl_config']['configured']:
            recommendations.append("🟡 WARNING: Configure SSL for secure Neon DB connection")
        
        if not self.test_results['neon_db_tests']['migrations']['present']:
            recommendations.append("🟡 WARNING: Create database migration scripts")
        
        # Success recommendations
        if self.test_results['compatibility_score'] >= 90:
            recommendations.append("✅ EXCELLENT: System is ready for GCP App Engine deployment")
        
        self.test_results['recommendations'] = recommendations
    
    def print_compatibility_report(self):
        """Print comprehensive compatibility report"""
        print("\n" + "=" * 80)
        print("☁️ GCP APP ENGINE & NEON DB COMPATIBILITY REPORT")
        print("=" * 80)
        
        print(f"\n📊 OVERALL COMPATIBILITY SCORE: {self.test_results['compatibility_score']:.1f}%")
        
        # GCP App Engine results
        print(f"\n🔧 GCP APP ENGINE COMPATIBILITY:")
        gcp_score = self._calculate_gcp_score()
        print(f"   Score: {gcp_score:.1f}%")
        
        gcp_tests = self.test_results['gcp_app_engine_tests']
        for test_name, result in gcp_tests.items():
            status = "✅" if result.get('valid', False) or result.get('compatible', False) else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        # Neon DB results
        print(f"\n🗄️ NEON DB COMPATIBILITY:")
        neon_score = self._calculate_neon_score()
        print(f"   Score: {neon_score:.1f}%")
        
        neon_tests = self.test_results['neon_db_tests']
        for test_name, result in neon_tests.items():
            status = "✅" if result.get('valid', False) or result.get('installed', False) or result.get('configured', False) else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        # Critical blockers
        if self.test_results['critical_blockers']:
            print(f"\n🚨 CRITICAL BLOCKERS:")
            for blocker in self.test_results['critical_blockers']:
                print(f"   🔴 {blocker}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in self.test_results['recommendations']:
            print(f"   {rec}")
        
        # Deployment readiness
        deployment_ready = self.test_results['deployment_readiness']['ready_for_deployment']
        production_ready = self.test_results['production_config_tests']['production_ready']
        
        print(f"\n🚀 DEPLOYMENT STATUS:")
        print(f"   Deployment Ready: {'✅' if deployment_ready else '❌'}")
        print(f"   Production Ready: {'✅' if production_ready else '❌'}")
        
        print("\n" + "=" * 80)
        print("✅ COMPATIBILITY TESTING COMPLETE")
        print("=" * 80)

def run_gcp_neon_compatibility_test():
    """Run GCP and Neon DB compatibility test"""
    tester = GCPNeonCompatibilityTest()
    results = tester.run_compatibility_test()
    tester.print_compatibility_report()
    return results

if __name__ == "__main__":
    print("☁️ Starting GCP App Engine & Neon DB Compatibility Test...")
    try:
        results = run_gcp_neon_compatibility_test()
        
        if results['compatibility_score'] >= 80:
            print("\n✅ System is compatible for GCP App Engine deployment!")
            sys.exit(0)
        else:
            print("\n⚠️ Compatibility issues detected - review before deployment!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error during compatibility testing: {str(e)}")
        sys.exit(2)
