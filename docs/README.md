# Documentation

Project documentation organized by file type following industry standards.

## Structure

```
docs/
├── README.md           # This file
├── md/                 # Markdown documentation
│   ├── SUPABASE_SETUP.md
│   └── TESTING.md
├── sql/                # SQL scripts and migrations
│   ├── 001_add_user_id.sql
│   └── supabase-setup.sql
└── examples/           # Example/test data files
    └── test_leads.csv
```

## Naming Conventions

### Markdown Files (`/md`)
- Use SCREAMING_SNAKE_CASE for guides: `SUPABASE_SETUP.md`
- Use lowercase for general docs: `api-reference.md`

### SQL Files (`/sql`)
- Migrations: `XXX_description.sql` (e.g., `001_add_user_id.sql`)
- Setup scripts: `service-setup.sql` (e.g., `supabase-setup.sql`)
- Always increment migration numbers sequentially

### Example Files (`/examples`)
- Test data: `test_*.csv`, `sample_*.json`
- Example configurations: `example-*.config`
- Keep files small and representative

## Usage

### Markdown Documentation
- **Setup Guides**: Step-by-step configuration instructions
- **Testing**: Testing procedures and guidelines
- **API Docs**: API endpoint documentation

### SQL Scripts
- **Migrations**: Database schema changes (run in order)
- **Setup**: Initial database configuration scripts
- **Seeds**: Test data (if needed)

## Adding New Documentation

### New Markdown Doc:
1. Create file in `/docs/md/`
2. Use appropriate naming convention
3. Update this README if needed

### New SQL Script:
1. Create file in `/docs/sql/`
2. Use sequential numbering for migrations
3. Add description in filename
4. Update this README if needed
