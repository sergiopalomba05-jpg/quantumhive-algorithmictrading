export function unpackPathComponent(pathComponent: any): { position: { x: number; y: number } } {
  // Función auxiliar para desempaquetar componentes de ruta
  if (typeof pathComponent === 'string') {
    const parts = pathComponent.split(',');
    return {
      position: {
        x: parseFloat(parts[0]) || 0,
        y: parseFloat(parts[1]) || 0,
      },
    };
  }
  if (pathComponent && typeof pathComponent === 'object') {
    return {
      position: {
        x: pathComponent.x || 0,
        y: pathComponent.y || 0,
      },
    };
  }
  return {
    position: { x: 0, y: 0 },
  };
}
