import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './NotFound.module.css';
import Button from '../components/ui/Button/Button'

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className={`${styles.container} page-container`}>
      <div className={styles.errorCode}>404</div>
      <h1 className={styles.title}>页面未找到</h1>
      <p className={styles.description}>你似乎迷失在了算法大陆的迷雾中，这片区域尚未被探索。</p>
      <div className={styles.homeButton}>
        <Button variant="primary" icon="🏠" onClick={() => navigate('/')}>
          返回首页
        </Button>
      </div>
    </div>
  );
};

export default NotFound;
