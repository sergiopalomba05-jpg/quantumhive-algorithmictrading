/**
 * QuantumCanvas - Canvas responsivo con soporte táctil para móvil
 * Implementa pinch-to-zoom y drag suave en pantallas táctiles
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useGesture } from '@use-gesture/react';

interface QuantumCanvasProps {
  width: number;
  height: number;
  children: React.ReactNode;
  onZoom?: (scale: number) => void;
  onPan?: (x: number, y: number) => void;
}

export const QuantumCanvas: React.FC<QuantumCanvasProps> = ({
  width,
  height,
  children,
  onZoom,
  onPan,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [isMobile, setIsMobile] = useState(false);

  // Detectar si es dispositivo móvil
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(
        'ontouchstart' in window ||
        navigator.maxTouchPoints > 0 ||
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
          navigator.userAgent
        )
      );
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Configurar canvas responsivo
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const updateCanvasSize = () => {
      const container = canvas.parentElement;
      if (container) {
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;

        // En móvil, usar ancho completo del contenedor
        const canvasWidth = isMobile ? containerWidth : Math.min(width, containerWidth);
        const canvasHeight = isMobile ? containerHeight : Math.min(height, containerHeight);

        canvas.width = canvasWidth;
        canvas.height = canvasHeight;

        // Ajustar escala inicial para que todo el mapa sea visible
        const scaleX = canvasWidth / width;
        const scaleY = canvasHeight / height;
        const initialScale = Math.min(scaleX, scaleY, 1);

        setTransform({ x: 0, y: 0, scale: initialScale });
      }
    };

    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);
    return () => window.removeEventListener('resize', updateCanvasSize);
  }, [width, height, isMobile]);

  // Gestos táctiles con react-use-gesture
  const bind = useGesture(
    {
      onDrag: ({ offset: [x, y] }) => {
        setTransform((prev) => {
          const newX = x;
          const newY = y;
          onPan?.(newX, newY);
          return { ...prev, x: newX, y: newY };
        });
      },
      onPinch: ({ offset: [d, a], origin: [ox, oy] }) => {
        // d = distance (zoom), a = angle (rotación), ox/oy = origen
        const newScale = Math.max(0.5, Math.min(3, d / 200 + 1));
        setTransform((prev) => ({
          ...prev,
          scale: newScale,
          x: ox - (ox - prev.x) * (newScale / prev.scale),
          y: oy - (oy - prev.y) * (newScale / prev.scale),
        }));
        onZoom?.(newScale);
      },
      onWheel: ({ offset: [, s] }) => {
        // Zoom con rueda del mouse (desktop)
        const newScale = Math.max(0.5, Math.min(3, transform.scale + s * -0.001));
        setTransform((prev) => ({ ...prev, scale: newScale }));
        onZoom?.(newScale);
      },
    },
    {
      target: canvasRef,
      drag: {
        from: () => [transform.x, transform.y],
        pinch: {
          from: () => [transform.scale * 200, 0, transform.x, transform.y],
        },
      },
    }
  );

  // Doble tap para resetear zoom
  const handleDoubleClick = useCallback(() => {
    const container = canvasRef.current?.parentElement;
    if (container) {
      const containerWidth = container.clientWidth;
      const containerHeight = container.clientHeight;
      const scaleX = containerWidth / width;
      const scaleY = containerHeight / height;
      const initialScale = Math.min(scaleX, scaleY, 1);

      setTransform({ x: 0, y: 0, scale: initialScale });
      onZoom?.(initialScale);
    }
  }, [width, height, onZoom]);

  return (
    <div
      className="quantum-canvas-container"
      style={{
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        touchAction: 'none', // Importante para gestos táctiles
        position: 'relative',
      }}
    >
      <canvas
        ref={canvasRef}
        {...bind()}
        onDoubleClick={handleDoubleClick}
        style={{
          width: '100%',
          height: '100%',
          cursor: isMobile ? 'grab' : 'grab',
          touchAction: 'none',
          WebkitTouchCallout: 'none',
          WebkitUserSelect: 'none',
          userSelect: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 10,
          right: 10,
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '8px',
          fontSize: isMobile ? '12px' : '14px',
          pointerEvents: 'none',
          zIndex: 1000,
        }}
      >
        Zoom: {(transform.scale * 100).toFixed(0)}%
      </div>
      {isMobile && (
        <div
          style={{
            position: 'absolute',
            bottom: 20,
            left: 20,
            background: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            pointerEvents: 'none',
            zIndex: 1000,
          }}
        >
          Pinch para zoom • Drag para mover
        </div>
      )}
    </div>
  );
};

/**
 * Hook personalizado para controlar el canvas
 */
export const useQuantumCanvas = () => {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleZoom = useCallback((newScale: number) => {
    setScale(newScale);
  }, []);

  const handlePan = useCallback((x: number, y: number) => {
    setPosition({ x, y });
  }, []);

  const resetView = useCallback(() => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  }, []);

  return {
    scale,
    position,
    handleZoom,
    handlePan,
    resetView,
  };
};

/**
 * Componente de controles de zoom para móvil
 */
export const ZoomControls: React.FC<{
  scale: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
}> = ({ scale, onZoomIn, onZoomOut, onReset }) => {
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 20,
        right: 20,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        zIndex: 1000,
      }}
    >
      <button
        onClick={onZoomIn}
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          border: 'none',
          fontSize: '24px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          touchAction: 'manipulation',
        }}
        aria-label="Zoom in"
      >
        +
      </button>
      <button
        onClick={onZoomOut}
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          border: 'none',
          fontSize: '24px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          touchAction: 'manipulation',
        }}
        aria-label="Zoom out"
      >
        −
      </button>
      <button
        onClick={onReset}
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          border: 'none',
          fontSize: '16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          touchAction: 'manipulation',
        }}
        aria-label="Reset view"
      >
        ⟲
      </button>
    </div>
  );
};
