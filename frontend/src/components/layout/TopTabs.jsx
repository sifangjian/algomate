import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Icon } from '../ui/Icons'
import { cardService } from '../../services/cardService'
import useDebounce from '../../hooks/useDebounce'
import styles from './TopTabs.module.css'

const tabs = [
    { id: 'workbench', label: '工作台', icon: 'grid', path: '/hall' },
    { id: 'review', label: '修炼', icon: 'menu', path: '/review' },
]

export default function TopTabs() {
    const navigate = useNavigate()
    const location = useLocation()
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState(null)
    const [showDropdown, setShowDropdown] = useState(false)
    const [searching, setSearching] = useState(false)
    const searchRef = useRef(null)
    const debouncedQuery = useDebounce(searchQuery, 300)

    const isActive = (path) => {
        if (path === '/hall' || path === '/') {
            return location.pathname === '/' || location.pathname === '/hall' || location.pathname === ''
        }
        return location.pathname.startsWith(path)
    }

    useEffect(() => {
        if (!debouncedQuery || debouncedQuery.trim().length < 1) {
            setSearchResults(null)
            setShowDropdown(false)
            return
        }

        let cancelled = false
        setSearching(true)

        async function doSearch() {
            try {
                const data = await cardService.searchCards(debouncedQuery.trim())
                if (!cancelled) {
                    setSearchResults(data)
                    setShowDropdown(true)
                }
            } catch (err) {
                if (!cancelled) {
                    setSearchResults(null)
                    console.error('Search failed:', err.message || err)
                }
            } finally {
                if (!cancelled) setSearching(false)
            }
        }

        doSearch()
        return () => { cancelled = true }
    }, [debouncedQuery])

    useEffect(() => {
        function handleClickOutside(e) {
            if (searchRef.current && !searchRef.current.contains(e.target)) {
                setShowDropdown(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const handleResultClick = useCallback((cardType, id) => {
        setShowDropdown(false)
        setSearchQuery('')
        setSearchResults(null)
        navigate(`/card/${cardType}/${id}`)
    }, [navigate])

    const handleInputChange = useCallback((e) => {
        setSearchQuery(e.target.value)
    }, [])

    const handleInputFocus = useCallback(() => {
        if (searchResults) {
            setShowDropdown(true)
        }
    }, [searchResults])

    const totalResults = searchResults
        ? (searchResults.problems?.length || 0) + (searchResults.solutions?.length || 0) + (searchResults.techniques?.length || 0)
        : 0

    return (
        <div className={styles.topTabs}>
            <div className={styles.tabsLeft}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        className={`${styles.tab} ${isActive(tab.path) ? styles.active : ''}`}
                        onClick={() => navigate(tab.path)}
                    >
                        <span className={styles.tabIcon}>
                            <Icon name={tab.icon} size={16} />
                        </span>
                        <span className={styles.tabLabel}>{tab.label}</span>
                    </button>
                ))}
            </div>
            <div className={styles.spacer} />
            <div className={styles.tabsRight}>
                <div className={styles.searchWrapper} ref={searchRef}>
                    <div className={styles.searchBox}>
                        <span className={styles.searchIcon}>
                            <Icon name="search" size={14} color="var(--text-muted)" />
                        </span>
                        <input
                            type="text"
                            className={styles.searchInput}
                            placeholder="搜索题目、解法、技巧..."
                            value={searchQuery}
                            onChange={handleInputChange}
                            onFocus={handleInputFocus}
                        />
                        {searching && <span className={styles.searchingIndicator}>···</span>}
                    </div>
                    {showDropdown && searchResults && totalResults > 0 && (
                        <div className={styles.searchDropdown}>
                            {searchResults.problems?.length > 0 && (
                                <div className={styles.dropdownGroup}>
                                    <div className={styles.dropdownGroupLabel}>📝 题目</div>
                                    {searchResults.problems.map((p) => (
                                        <div
                                            key={`problem-${p.id}`}
                                            className={styles.dropdownItem}
                                            onClick={() => handleResultClick('problem', p.id)}
                                        >
                                            <span className={styles.dropdownItemName}>{p.name}</span>
                                            {p.difficulty && (
                                                <span className={`${styles.dropdownBadge} ${styles[`diff${p.difficulty}`]}`}>
                                                    {p.difficulty}
                                                </span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                            {searchResults.solutions?.length > 0 && (
                                <div className={styles.dropdownGroup}>
                                    <div className={styles.dropdownGroupLabel}>💡 解法</div>
                                    {searchResults.solutions.map((s) => (
                                        <div
                                            key={`solution-${s.id}`}
                                            className={styles.dropdownItem}
                                            onClick={() => handleResultClick('solution', s.id)}
                                        >
                                            <span className={styles.dropdownItemName}>{s.name}</span>
                                            {s.problem_title && (
                                                <span className={styles.dropdownItemMeta}>{s.problem_title}</span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                            {searchResults.techniques?.length > 0 && (
                                <div className={styles.dropdownGroup}>
                                    <div className={styles.dropdownGroupLabel}>⭐ 技巧</div>
                                    {searchResults.techniques.map((t) => (
                                        <div
                                            key={`technique-${t.id}`}
                                            className={styles.dropdownItem}
                                            onClick={() => handleResultClick('technique', t.id)}
                                        >
                                            <span className={styles.dropdownItemName}>{t.name}</span>
                                            {t.category && (
                                                <span className={styles.dropdownItemMeta}>{t.category}</span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                    {showDropdown && searchResults && totalResults === 0 && debouncedQuery.trim().length >= 1 && (
                        <div className={styles.searchDropdown}>
                            <div className={styles.dropdownEmpty}>未找到匹配结果</div>
                        </div>
                    )}
                </div>
                <button className={styles.settingsBtn} title="设置">
                    <Icon name="gear" size={14} />
                </button>
            </div>
        </div>
    )
}