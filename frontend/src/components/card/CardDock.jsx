import { useState, useCallback, useRef, useMemo } from 'react'
import { createPortal } from 'react-dom'
import styles from './CardDock.module.css'

const MAX_VISIBLE = 15

export default function CardDock({ cards, onCardClick }) {
    const cardRefs = useRef({})
    const [searchTerm, setSearchTerm] = useState('')
    const [searchFocused, setSearchFocused] = useState(false)

    const filteredCards = useMemo(() => {
        if (!cards || cards.length === 0) return []
        const term = searchTerm.trim().toLowerCase()
        const filtered = term
            ? cards.filter(c => c.name.toLowerCase().includes(term))
            : cards
        return term ? filtered : filtered.slice(0, MAX_VISIBLE)
    }, [cards, searchTerm])

    const handleClick = useCallback((card) => {
        const el = cardRefs.current[card.id]
        if (el) {
            const rect = el.getBoundingClientRect()
            onCardClick?.(card, rect)
        }
    }, [onCardClick])

    const active = searchFocused || searchTerm.trim()

    if (!cards || cards.length === 0) return null

    return createPortal(
        <div className={`${styles.dockContainer} ${active ? styles.dockActive : ''}`}>
            <div className={`${styles.searchWrapper} ${active ? styles.searchActive : ''}`}>
                <input
                    className={styles.searchInput}
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onFocus={() => setSearchFocused(true)}
                    onBlur={() => setSearchFocused(false)}
                    placeholder="搜索..."
                    aria-label="搜索卡牌"
                />
            </div>

            <div className={styles.cardList}>
                {filteredCards.map((card) => (
                    <div key={card.id} className={styles.cardWrapper}>
                        <div
                            ref={(el) => { cardRefs.current[card.id] = el }}
                            className={styles.thumbnail}
                            onClick={() => handleClick(card)}
                            title={card.name}
                        >
                            <span className={styles.thumbnailIcon}>📜</span>
                            <span className={styles.thumbnailName}>{card.name}</span>
                        </div>
                    </div>
                ))}
                {filteredCards.length === 0 && searchTerm.trim() && (
                    <div className={styles.emptyHint}>
                        <span className={styles.emptyIcon}>🔍</span>
                    </div>
                )}
            </div>
        </div>,
        document.body
    )
}
