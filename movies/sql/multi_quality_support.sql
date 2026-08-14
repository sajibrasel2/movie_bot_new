-- Add multi-quality support to movies table
-- Each quality has its own download links and size

ALTER TABLE mlsbd_movies
ADD COLUMN IF NOT EXISTS available_qualities JSON COMMENT 'Array of available qualities with their details',
ADD COLUMN IF NOT EXISTS base_movie_title VARCHAR(500) COMMENT 'Movie title without quality suffix',
ADD COLUMN IF NOT EXISTS quality_variants JSON COMMENT 'JSON object with quality-specific data';

-- Example structure for quality_variants:
-- {
--   "720p": {
--     "size": "1.2 GB",
--     "download_links": {
--       "gdflix": "https://...",
--       "hubcloud": "https://..."
--     }
--   },
--   "1080p": {
--     "size": "2.5 GB",
--     "download_links": {
--       "gdflix": "https://...",
--       "hubcloud": "https://..."
--     }
--   }
-- }

-- Function to merge duplicate movies by base title
-- This will be handled by Python script
