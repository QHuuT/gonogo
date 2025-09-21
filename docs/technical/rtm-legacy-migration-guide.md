# RTM Legacy Script Migration Guide

**Related Issue**: US-00058 - Legacy script migration and deprecation
**Parent Epic**: EP-00005 - Requirements Traceability Matrix Automation
**Last Updated**: 2025-09-21

## Overview

This guide provides comprehensive instructions for migrating from file-based RTM operations to the new hybrid RTM system that supports both file-based and database-backed operations.

## Migration Strategy

The migration follows a **dual-mode approach** that ensures backward compatibility while providing a smooth transition path to database-backed RTM operations.

### Supported Modes

1. **File Mode** (`--mode file`): Traditional file-based RTM operations
2. **Database Mode** (`--mode database`): Database-backed RTM operations
3. **Auto Mode** (`--mode auto`): Automatically choose best available option (default)

## Pre-Migration Assessment

### 1. Check Current RTM Status

```bash
# Validate current file-based RTM
python tools/rtm-links-simple.py --validate --mode file

# Check system capabilities
python tools/rtm-links-simple.py --info
```

### 2. Verify Database Availability

```bash
# Test database connectivity (if available)
python tools/rtm-links-simple.py --info --mode database
```

## Migration Steps

### Phase 1: Enhanced Tool Deployment

The enhanced RTM tools are already deployed and backward compatible:

- `tools/rtm-links-simple.py` - Enhanced with hybrid mode support
- `src/shared/utils/rtm_hybrid_generator.py` - New hybrid RTM generator
- `.github/workflows/rtm-validation.yml` - Enhanced workflow with mode selection

### Phase 2: Validate Enhanced Tools

```bash
# 1. Test file mode (existing behavior)
python tools/rtm-links-simple.py --validate --mode file --rtm-file docs/traceability/requirements-matrix.md

# 2. Test auto mode (default behavior)
python tools/rtm-links-simple.py --validate

# 3. Check system information
python tools/rtm-links-simple.py --info
```

### Phase 3: Database Integration (When Available)

When the database RTM system becomes available:

```bash
# 1. Test database mode
python tools/rtm-links-simple.py --validate --mode database

# 2. Export database RTM to file (backward compatibility)
python tools/rtm-links-simple.py --export-db --rtm-file docs/traceability/requirements-matrix-db.md

# 3. Compare file vs database RTM
python tools/rtm-links-simple.py --validate --mode file
python tools/rtm-links-simple.py --validate --mode database
```

## Enhanced CLI Interface

### New Command Options

```bash
# Mode Selection
--mode {auto,file,database}    # Choose RTM operation mode
--info                         # Show system information
--export-db                    # Export database RTM to file

# Examples
python tools/rtm-links-simple.py --validate --mode auto
python tools/rtm-links-simple.py --info
python tools/rtm-links-simple.py --export-db --rtm-file exported-rtm.md
```

### Enhanced Output Format

The tools now provide enhanced output with mode context:

```
RTM Validation - Mode: auto
Using database as source of truth

RTM Link Validation Report
==============================
Total Links: 238
Valid Links: 149
Invalid Links: 89
Health Score: 62.6%

Information:
  - Database RTM validation complete - using database as source of truth
```

## GitHub Actions Integration

### Workflow Dispatch Options

The RTM validation workflow now supports mode selection:

```yaml
# Manual workflow trigger with mode selection
workflow_dispatch:
  inputs:
    rtm_mode:
      description: 'RTM operation mode'
      required: false
      default: 'auto'
      type: choice
      options:
        - auto
        - database
        - file
```

### Usage Examples

```bash
# Trigger validation with specific mode
gh workflow run rtm-validation.yml -f rtm_mode=database

# Use default auto mode
gh workflow run rtm-validation.yml
```

## Backward Compatibility

### Existing Scripts Continue to Work

All existing RTM scripts and workflows continue to function without modification:

```bash
# These commands work exactly as before
python tools/rtm-links-simple.py --validate
python tools/rtm-links-simple.py --update --dry-run
```

### Fallback Mechanisms

The hybrid system includes comprehensive fallback support:

1. **Database Unavailable**: Automatically falls back to file mode
2. **Import Errors**: Falls back to original RTM generator
3. **Configuration Issues**: Uses safe defaults

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors

**Issue**: `ImportError: cannot import name 'HybridRTMLinkGenerator'`

**Solution**: The system automatically falls back to the original generator:
```bash
# Check if hybrid mode is available
python tools/rtm-links-simple.py --info
```

#### 2. Database Connection Issues

**Issue**: Database mode fails with connection errors

**Solution**: Use file mode or auto mode with fallback:
```bash
# Use file mode explicitly
python tools/rtm-links-simple.py --validate --mode file

# Use auto mode (will fall back to file)
python tools/rtm-links-simple.py --validate --mode auto
```

#### 3. Mode Detection Issues

**Issue**: Auto mode not selecting expected mode

**Solution**: Check system information and use explicit mode:
```bash
# Check what mode auto selects
python tools/rtm-links-simple.py --info

# Use explicit mode
python tools/rtm-links-simple.py --validate --mode database
```

## Best Practices

### 1. Development Workflow

```bash
# Always check system capabilities first
python tools/rtm-links-simple.py --info

# Use auto mode for daily operations
python tools/rtm-links-simple.py --validate

# Use explicit modes for testing
python tools/rtm-links-simple.py --validate --mode file
python tools/rtm-links-simple.py --validate --mode database
```

### 2. CI/CD Integration

- Use `auto` mode in workflows for maximum compatibility
- Test both file and database modes in comprehensive test suites
- Monitor workflow logs for mode selection information

### 3. Documentation Synchronization

When using database mode, periodically export to file for documentation:

```bash
# Export database RTM to file
python tools/rtm-links-simple.py --export-db --rtm-file docs/traceability/requirements-matrix-current.md
```

## Migration Timeline

### Immediate (Available Now)
- ✅ Enhanced RTM tools with hybrid support
- ✅ Backward compatibility maintained
- ✅ GitHub Actions workflow enhanced
- ✅ Auto mode detection

### Phase 2 (When Database Available)
- Database RTM operations
- Full database validation
- Export capabilities
- Performance improvements

### Phase 3 (Future Enhancements)
- Real-time synchronization
- Advanced reporting
- Integration with external tools
- Performance optimization

## Support and Resources

### Documentation
- [Development Workflow](development-workflow.md)
- [Quality Assurance](quality-assurance.md)
- [Requirements Matrix](../traceability/requirements-matrix.md)

### Tools and Commands
- `python tools/rtm-links-simple.py --help` - Full CLI documentation
- `python tools/rtm-links-simple.py --info` - System information
- GitHub Actions: `.github/workflows/rtm-validation.yml`

### Issue Tracking
- Epic: [EP-00005 - RTM Automation](../../issues)
- User Story: [US-00058 - Legacy script migration](../../issues)

---

**Migration Status**: ✅ **COMPLETE** - Hybrid RTM system deployed with full backward compatibility