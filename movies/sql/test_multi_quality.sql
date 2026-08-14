-- Test multi-quality movie data for Malik
UPDATE mlsbd_movies 
SET quality_variants = JSON_OBJECT(
    '720p', JSON_OBJECT(
        'size', '1.2 GB',
        'download_links', JSON_OBJECT(
            'gdflix', 'https://example.com/malik-720p'
        )
    ),
    '1080p', JSON_OBJECT(
        'size', '2.5 GB',
        'download_links', JSON_OBJECT(
            'gdflix', 'https://example.com/malik-1080p',
            'hubcloud', 'https://example.com/malik-1080p-hub'
        )
    ),
    '480p', JSON_OBJECT(
        'size', '650 MB',
        'download_links', JSON_OBJECT(
            'gdflix', 'https://example.com/malik-480p'
        )
    )
),
available_qualities = JSON_ARRAY('1080p', '720p', '480p'),
base_movie_title = 'Malik (2026) Bengali WEB-DL'
WHERE id = 34;
