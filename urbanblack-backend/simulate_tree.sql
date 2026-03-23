CREATE TABLE IF NOT EXISTS mock_wallet (
    user_id BIGINT PRIMARY KEY,
    balance DECIMAL(15, 2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mock_users (
    id BIGINT PRIMARY KEY,
    active BOOLEAN DEFAULT TRUE
);

CREATE OR REPLACE FUNCTION simulate_node_insertion(p_user_id BIGINT)
RETURNS VOID AS $$
DECLARE
    v_new_bfs_pos BIGINT;
    v_current_parent_pos BIGINT;
    v_ancestor_user_id BIGINT;
    v_is_active BOOLEAN;
    v_level INT := 1;
BEGIN
    -- 1. Get next BFS position
    SELECT COALESCE(MAX(bfs_position), 0) + 1 INTO v_new_bfs_pos FROM reward_tree_nodes;

    -- 2. Insert node
    INSERT INTO reward_tree_nodes(user_id, bfs_position, parent_node_id, depth_level, active)
    VALUES (p_user_id, v_new_bfs_pos, FLOOR(v_new_bfs_pos / 2.0), FLOOR(LOG(2, v_new_bfs_pos)), TRUE);

    -- 3. Loop 9 times for ancestors
    v_current_parent_pos := FLOOR(v_new_bfs_pos / 2.0);

    WHILE v_level <= 9 LOOP
        v_is_active := FALSE;
        v_ancestor_user_id := NULL;

        IF v_current_parent_pos >= 1 THEN
            -- Find who owns the ancestor node
            SELECT user_id INTO v_ancestor_user_id FROM reward_tree_nodes WHERE bfs_position = v_current_parent_pos;
            
            -- If ancestor exists, check if they are active (default to active if not in mock_users)
            IF v_ancestor_user_id IS NOT NULL THEN
                SELECT COALESCE(active, TRUE) INTO v_is_active FROM mock_users WHERE id = v_ancestor_user_id;
                -- If not found in mock_users, assume active
                IF NOT FOUND THEN
                    v_is_active := TRUE;
                END IF;
            END IF;
        END IF;

        IF v_is_active THEN
            -- Pay user
            INSERT INTO mock_wallet(user_id, balance) VALUES (v_ancestor_user_id, 1)
            ON CONFLICT (user_id) DO UPDATE SET balance = mock_wallet.balance + 1;
        ELSE
            -- Pay Admin 
            INSERT INTO mock_wallet(user_id, balance) VALUES (0, 1)
            ON CONFLICT (user_id) DO UPDATE SET balance = mock_wallet.balance + 1;
        END IF;

        v_current_parent_pos := FLOOR(v_current_parent_pos / 2.0);
        v_level := v_level + 1;
    END LOOP;

    -- 4. Fixed ₹1 Admin Commission
    INSERT INTO mock_wallet(user_id, balance) VALUES (0, 1)
    ON CONFLICT (user_id) DO UPDATE SET balance = mock_wallet.balance + 1;

END;
$$ LANGUAGE plpgsql;
