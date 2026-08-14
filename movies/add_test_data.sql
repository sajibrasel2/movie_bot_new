-- Add test movie data for local testing
-- Run this to populate database with sample movies

USE techandc_prompts;

-- Insert test movies
INSERT INTO mlsbd_movies 
(movie_title, slug, mlsbd_url, gdflix_url, poster_url, quality, year, movie_size_readable, movie_size_bytes, status, download_links, is_featured, view_count)
VALUES 
(
    'Malik (2026) Bengali WEB-DL – 720P | 1080P',
    'malik-2026-bengali-web-dl-720p-1080p',
    'https://mlsbd.co/malik-2026-bengali/',
    'https://gdflix.dev/file/example123',
    'https://image.tmdb.org/t/p/w500/example1.jpg',
    '720p HD',
    2026,
    '1.2 GB',
    1288490188,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/example123","hubcloud":"https://hubcloud.pro/file/abc","filepress":"https://filepress.link/def"}',
    1,
    150
),
(
    'Heart Beat (2026) S03 Dual Audio [Hindi-Tamil]',
    'heart-beat-2026-s03-dual-audio-hindi-tamil',
    'https://mlsbd.co/heart-beat-2026/',
    'https://gdflix.dev/file/example456',
    'https://image.tmdb.org/t/p/w500/example2.jpg',
    '1080p Full HD',
    2026,
    '2.5 GB',
    2684354560,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/example456","multicloud":"https://multicloud.link/xyz"}',
    1,
    200
),
(
    'Johnny Jumper JHS ESub (2026) [720p HD]',
    'johnny-jumper-jhs-esub-2026-720p-hd',
    'https://mlsbd.co/johnny-jumper-2026/',
    'https://gdflix.dev/file/example789',
    'https://image.tmdb.org/t/p/w500/example3.jpg',
    '720p HD',
    2026,
    '850 MB',
    891289600,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/example789","filepress":"https://filepress.link/ghi"}',
    0,
    75
),
(
    'In the Grey Blu Ray ESub (2026) [720p HD]',
    'in-the-grey-blu-ray-esub-2026-720p-hd',
    'https://mlsbd.co/in-the-grey-2026/',
    'https://gdflix.dev/file/exampleabc',
    'https://image.tmdb.org/t/p/w500/example4.jpg',
    '720p HD',
    2026,
    '1.1 GB',
    1181116006,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/exampleabc","hubcloud":"https://hubcloud.pro/file/jkl"}',
    0,
    95
),
(
    'Atonko Season 1 Part 2 (2026) | Bangla Web Series',
    'atonko-season-1-part-2-2026-bangla-web-series',
    'https://mlsbd.co/atonko-season-1-part-2/',
    'https://gdflix.dev/file/exampledef',
    'https://image.tmdb.org/t/p/w500/example5.jpg',
    '1080p Full HD',
    2026,
    '3.2 GB',
    3435973836,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/exampledef","filepress":"https://filepress.link/mno","hubcloud":"https://hubcloud.pro/file/pqr"}',
    1,
    180
),
(
    'Rongin Shurma (2026) Bengali Chorki WEB-DL – 720P',
    'rongin-shurma-2026-bengali-chorki-web-dl-720p',
    'https://mlsbd.co/rongin-shurma-2026/',
    'https://gdflix.dev/file/exampleghi',
    'https://image.tmdb.org/t/p/w500/example6.jpg',
    '720p HD',
    2026,
    '750 MB',
    786432000,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/exampleghi","multicloud":"https://multicloud.link/stu"}',
    0,
    60
),
(
    'Saptadingar Guptodhon (2026) Bengali Hoichoi WEB-DL',
    'saptadingar-guptodhon-2026-bengali-hoichoi-web-dl',
    'https://mlsbd.co/saptadingar-guptodhon-2026/',
    'https://gdflix.dev/file/examplejkl',
    'https://image.tmdb.org/t/p/w500/example7.jpg',
    '1080p Full HD',
    2026,
    '1.8 GB',
    1932735283,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/examplejkl","filepress":"https://filepress.link/vwx"}',
    0,
    120
),
(
    'The Odyssey (2026) Hollywood Action Movie',
    'the-odyssey-2026-hollywood-action-movie',
    'https://mlsbd.co/the-odyssey-2026/',
    'https://gdflix.dev/file/examplemno',
    'https://image.tmdb.org/t/p/w500/example8.jpg',
    '1080p Full HD',
    2026,
    '2.8 GB',
    3006477107,
    'completed',
    '{"gdflix":"https://gdflix.dev/file/examplemno","hubcloud":"https://hubcloud.pro/file/yza"}',
    1,
    250
);

-- Check inserted data
SELECT id, movie_title, slug, quality, status, is_featured 
FROM mlsbd_movies 
WHERE status = 'completed'
ORDER BY id DESC;
