# 🎬 Movie Website - movies.techandclick.site

Netflix-style professional movie website with download links.

## 📋 Features

- ✅ Netflix-style dark theme
- ✅ Movie posters and details
- ✅ Multiple download sources (GDFlix, HubCloud, FilePress, MultiCloud)
- ✅ SEO-friendly URLs (`/movie-name-2026`)
- ✅ Search functionality
- ✅ View counter
- ✅ Featured movies section
- ✅ Responsive design (mobile-friendly)
- ✅ Fast loading with lazy images

## 🚀 Installation

### 1. Database Setup

Run the SQL migrations:

```bash
# SSH into server
cd ~/movie_bot_new/ftp_movie_bot

# Apply database schema
mysql -u techandc_bot -p'12345Sajibs6@' techandc_prompts < add_movie_website_columns.sql

# Generate slugs for existing movies
# Visit: https://techandclick.site/movie_bot_new/movies/migrate_slugs.php
```

### 2. Subdomain Setup

**cPanel → Subdomains:**
- Subdomain: `movies`
- Domain: `techandclick.site`
- Document Root: `/home/techandc/movie_bot_new/movies`

### 3. Configure Python Scripts

Update Telegram bot to send website links:

```bash
cd ~/movie_bot_new/ftp_movie_bot

# Test slug generator
python3 slug_generator.py

# Configure Telegram credentials in send_movie_to_telegram.py
nano send_movie_to_telegram.py
# Add your API_ID, API_HASH, SESSION_STRING
```

### 4. Update mlsbd_trigger.py

Already updated to generate slugs automatically for new movies.

## 📂 File Structure

```
movies/
├── index.php                 # Homepage (featured + recent movies)
├── movie.php                 # Single movie page
├── search.php                # Search results page
├── config.php                # Database & helper functions
├── migrate_slugs.php         # One-time migration script
├── .htaccess                 # Clean URLs & security
├── assets/
│   ├── css/
│   │   └── style.css         # Netflix-style CSS
│   ├── js/
│   │   └── main.js           # Interactions
│   └── images/
│       └── (favicon, etc.)
└── api/
    ├── get_movie.php         # Get movie by slug/id
    └── track_download.php    # Track download clicks
```

## 🔗 URL Structure

- Homepage: `https://movies.techandclick.site/`
- Movie Page: `https://movies.techandclick.site/movie-name-2026`
- Search: `https://movies.techandclick.site/search.php?q=malik`
- API: `https://movies.techandclick.site/api/get_movie.php?slug=malik-2026`

## 🤖 Telegram Integration

### Current Flow:
1. **mlsbd_trigger.py** scrapes MLSBD → creates movie with slug
2. **GitHub Actions** downloads & uploads movie parts
3. **send_movie_to_telegram.py** sends poster + "Watch Now" button to Telegram

### Telegram Message Format:
```
🎬 Malik (2026) Bengali WEB-DL

📺 Quality: 720p HD
📅 Year: 2026
💾 Size: 1.2 GB

🔗 Watch & Download:
👇 Click the button below

[🎬 Watch Now] → https://movies.techandclick.site/malik-2026-bengali
```

## 🛠️ Maintenance

### Add Featured Movie:
```sql
UPDATE mlsbd_movies 
SET is_featured = 1 
WHERE id = 123;
```

### Check View Stats:
```sql
SELECT movie_title, view_count, slug
FROM mlsbd_movies 
WHERE status = 'completed'
ORDER BY view_count DESC 
LIMIT 10;
```

### Regenerate Slug:
```sql
UPDATE mlsbd_movies 
SET slug = 'new-slug-here' 
WHERE id = 123;
```

## 🔒 Security

- ✅ SQL injection protected (PDO prepared statements)
- ✅ XSS protected (htmlspecialchars on all outputs)
- ✅ CSRF protection ready (can be added later)
- ✅ Config file access blocked (.htaccess)
- ✅ Directory listing disabled
- ✅ Security headers enabled

## 📊 Analytics (Future)

Can add:
- Google Analytics
- Download tracking per source
- Popular movies widget
- Recent searches

## 🎨 Customization

### Change Theme Color:
Edit `assets/css/style.css`:
```css
:root {
    --netflix-red: #E50914;  /* Change this */
}
```

### Change Site Name:
Edit `config.php`:
```php
define('SITE_NAME', 'Your Site Name');
```

## 🐛 Troubleshooting

### Movies not showing?
Check:
1. Database has movies with `status='completed'`
2. Movies have `poster_url` and `slug`
3. Run `migrate_slugs.php` to generate slugs

### Images not loading?
- Check poster URLs are accessible
- Try different image (some MLSBD posters may be blocked)

### Clean URLs not working?
- Check `.htaccess` is uploaded
- Verify `mod_rewrite` is enabled in Apache
- Check subdomain points to correct directory

## 📝 License

Proprietary - TechAndClick.site

## 👤 Author

AI Assistant + Sajib Rasel
