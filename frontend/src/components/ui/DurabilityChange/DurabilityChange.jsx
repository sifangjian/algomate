import { useEffect, useState } from 'react'
import styles from './DurabilityChange.module.css'

export default function DurabilityChange({ value, onDone }) {
    const [visible, setVisible] = useState(true)

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false)
            onDone?.()
        }, 1500)
        return () => clearTimeout(timer)
    }, [onDone])

    if (!visible) return null

    const isPositive = value > 0

    return (
        <div className={`${styles.container} ${isPositive ? styles.positive : styles.negative}`}>
            {isPositive ? '+' : ''}{value}
        </div>
    )
}
