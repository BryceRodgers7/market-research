-- Query to identify the worst performing names based on exposure vs votes gap
-- A name is "exposed" when someone sees it on a form (whether they vote for it or not)
-- The gap between exposures and votes shows which names are being seen but not chosen

-- For a specific question (replace {question_num} with 1-5):
WITH name_exposures AS (
    -- Count how many times each name was exposed (shown on a form that was submitted)
    SELECT 
        name,
        COUNT(*) as exposure_count
    FROM (
        -- Form 1: Philanthrifind, Give-io, Donathropy, Kinderfully
        SELECT 'Philanthrifind' as name, form_id FROM submissions WHERE form_id = 1
        UNION ALL
        SELECT 'Give-io' as name, form_id FROM submissions WHERE form_id = 1
        UNION ALL
        SELECT 'Donathropy' as name, form_id FROM submissions WHERE form_id = 1
        UNION ALL
        SELECT 'Kinderfully' as name, form_id FROM submissions WHERE form_id = 1
        
        -- Form 2: Philanthrifound, Causenex, Givanthropy, Tomatchin
        UNION ALL
        SELECT 'Philanthrifound' as name, form_id FROM submissions WHERE form_id = 2
        UNION ALL
        SELECT 'Causenex' as name, form_id FROM submissions WHERE form_id = 2
        UNION ALL
        SELECT 'Givanthropy' as name, form_id FROM submissions WHERE form_id = 2
        UNION ALL
        SELECT 'Tomatchin' as name, form_id FROM submissions WHERE form_id = 2
        
        -- Form 3: Philanthri, Give Connects, Donanthropy, Humanitable
        UNION ALL
        SELECT 'Philanthri' as name, form_id FROM submissions WHERE form_id = 3
        UNION ALL
        SELECT 'Give Connects' as name, form_id FROM submissions WHERE form_id = 3
        UNION ALL
        SELECT 'Donanthropy' as name, form_id FROM submissions WHERE form_id = 3
        UNION ALL
        SELECT 'Humanitable' as name, form_id FROM submissions WHERE form_id = 3
        
        -- Form 4: Givio Gives, Philanthrifound, Givanthropy, Humanitable
        UNION ALL
        SELECT 'Givio Gives' as name, form_id FROM submissions WHERE form_id = 4
        UNION ALL
        SELECT 'Philanthrifound' as name, form_id FROM submissions WHERE form_id = 4
        UNION ALL
        SELECT 'Givanthropy' as name, form_id FROM submissions WHERE form_id = 4
        UNION ALL
        SELECT 'Humanitable' as name, form_id FROM submissions WHERE form_id = 4
        
        -- Form 5: Give Connects, Philanthrifind, Give-io, Tomatchin
        UNION ALL
        SELECT 'Give Connects' as name, form_id FROM submissions WHERE form_id = 5
        UNION ALL
        SELECT 'Philanthrifind' as name, form_id FROM submissions WHERE form_id = 5
        UNION ALL
        SELECT 'Give-io' as name, form_id FROM submissions WHERE form_id = 5
        UNION ALL
        SELECT 'Tomatchin' as name, form_id FROM submissions WHERE form_id = 5
        
        -- Form 6: Philanthri, Givio Gives, Kinderfully, Causenex
        UNION ALL
        SELECT 'Philanthri' as name, form_id FROM submissions WHERE form_id = 6
        UNION ALL
        SELECT 'Givio Gives' as name, form_id FROM submissions WHERE form_id = 6
        UNION ALL
        SELECT 'Kinderfully' as name, form_id FROM submissions WHERE form_id = 6
        UNION ALL
        SELECT 'Causenex' as name, form_id FROM submissions WHERE form_id = 6
    ) AS all_exposures
    GROUP BY name
),
name_votes AS (
    -- Count how many votes each name received for this specific question
    SELECT 
        question_{question_num}_answer as name,
        COUNT(*) as vote_count
    FROM submissions
    GROUP BY question_{question_num}_answer
)
SELECT 
    ne.name,
    ne.exposure_count,
    COALESCE(nv.vote_count, 0) as vote_count,
    ne.exposure_count - COALESCE(nv.vote_count, 0) as gap
FROM name_exposures ne
LEFT JOIN name_votes nv ON ne.name = nv.name
ORDER BY gap DESC, ne.name
LIMIT 3;
