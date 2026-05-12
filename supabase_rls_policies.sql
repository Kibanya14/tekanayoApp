-- POLITIQUES SIMPLIFIÉES POUR SUPABASE STORAGE
-- À créer dans Storage → uploads → Policies (interface graphique)

-- =====================================================
-- POLITIQUE 1: Fichiers PUBLICS (tout le monde peut lire)
-- =====================================================
-- Dans l'interface : Storage → uploads → Policies → + New policy
-- Type: SELECT (lecture)
-- Policy name: Public files
-- Allowed condition:
-- bucket_id = 'uploads' AND name LIKE 'public/%'

-- =====================================================
-- POLITIQUE 2: Fichiers SEMI-PRIVÉS (utilisateurs loggés)
-- =====================================================
-- Type: SELECT (lecture)
-- Policy name: Semi-private files
-- Allowed condition:
-- bucket_id = 'uploads' AND name LIKE 'semi_private/%' AND auth.role() = 'authenticated'

-- =====================================================
-- POLITIQUE 3: Fichiers PRIVÉS (admins seulement)
-- =====================================================
-- Type: SELECT (lecture)
-- Policy name: Private seller documents
-- Allowed condition:
-- bucket_id = 'uploads' AND name LIKE 'private/%' AND auth.jwt() ->> 'role' = 'service_role'

-- =====================================================
-- POLITIQUE 4: UPLOAD (qui peut uploader)
-- =====================================================
-- Type: INSERT (écriture)
-- Policy name: Allow uploads
-- Allowed condition:
-- bucket_id = 'uploads' AND auth.role() = 'authenticated'

-- =====================================================
-- POLITIQUE 5: SUPPRESSION (qui peut supprimer)
-- =====================================================
-- Type: DELETE (suppression)
-- Policy name: Allow deletions
-- Allowed condition:
-- bucket_id = 'uploads' AND auth.role() = 'authenticated'