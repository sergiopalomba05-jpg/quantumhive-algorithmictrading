import { useRef, useState, useCallback } from 'react';
import PixiGame from './PixiGame.tsx';

import { useElementSize } from 'usehooks-ts';
import { Stage } from '@pixi/react';
import { ConvexProvider, useConvex, useQuery } from 'convex/react';
import PlayerDetails from './PlayerDetails.tsx';
import { api } from '../../convex/_generated/api';
import { useWorldHeartbeat } from '../hooks/useWorldHeartbeat.ts';
import { useHistoricalTime } from '../hooks/useHistoricalTime.ts';
import { GameId } from '../../convex/aiTown/ids.ts';
import { useServerGame } from '../hooks/serverGame.ts';
import InteractButton from './buttons/InteractButton.tsx';
import Button from './buttons/Button.tsx';

export const SHOW_DEBUG_UI = !!import.meta.env.VITE_SHOW_DEBUG_UI;

export default function Game({
  helpModalOpen,
  setHelpModalOpen,
}: {
  helpModalOpen: boolean;
  setHelpModalOpen: (v: boolean) => void;
}) {
  const convex = useConvex();
  const [selectedElement, setSelectedElement] = useState<{
    kind: 'player';
    id: GameId<'players'>;
  }>();
  const [gameWrapperRef, { width, height }] = useElementSize();

  const worldStatus = useQuery(api.world.defaultWorldStatus);
  const worldId = worldStatus?.worldId;
  const engineId = worldStatus?.engineId;

  const game = useServerGame(worldId);

  useWorldHeartbeat();

  const worldState = useQuery(api.world.worldState, worldId ? { worldId } : 'skip');
  const { historicalTime, timeManager } = useHistoricalTime(worldState?.engine);

  const [panelOpen, setPanelOpen] = useState(true);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }, []);

  if (!worldId || !engineId || !game) {
    return (
      <div className="flex-1 flex items-center justify-center text-white text-2xl font-body">
        Cargando QuantumHive Town...
      </div>
    );
  }

  return (
    <>
      <div className="flex-1 flex relative overflow-hidden">
        {/* Game area */}
        <div
          className={`relative overflow-hidden transition-all duration-300 ${panelOpen ? 'w-[calc(100%-380px)]' : 'w-full'}`}
          ref={gameWrapperRef}
        >
          <div className="absolute inset-0">
            <div className="container">
              <Stage width={width} height={height} options={{ backgroundColor: 0x0a0a1a }}>
                <ConvexProvider client={convex}>
                  <PixiGame
                    game={game}
                    worldId={worldId}
                    engineId={engineId}
                    width={width}
                    height={height}
                    historicalTime={historicalTime}
                    setSelectedElement={setSelectedElement}
                  />
                </ConvexProvider>
              </Stage>
            </div>
          </div>

          {/* HUD Overlay */}
          <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
            <h1 className="text-3xl font-bold font-display game-title drop-shadow-lg">
              QuantumHive Town
            </h1>
          </div>

          {/* Bottom controls */}
          <div className="absolute bottom-4 left-4 z-10 flex gap-2">
            <InteractButton />
            <Button onClick={toggleFullscreen}>Pantalla Completa</Button>
            <Button onClick={() => setPanelOpen(!panelOpen)}>
              {panelOpen ? 'Ocultar Panel' : 'Mostrar Panel'}
            </Button>
            <Button onClick={() => setHelpModalOpen(true)}>Help</Button>
          </div>
        </div>

        {/* Right panel */}
        {panelOpen && (
          <div className="w-[380px] shrink-0 flex flex-col overflow-y-auto bg-brown-800 text-brown-100 border-l-4 border-brown-900">
            <div className="p-4 border-b-2 border-brown-900 flex justify-between items-center">
              <h2 className="text-xl font-display game-title">Agentes</h2>
              <button
                onClick={() => setPanelOpen(false)}
                className="text-brown-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <PlayerDetails
                worldId={worldId}
                engineId={engineId}
                game={game}
                playerId={selectedElement?.id}
                setSelectedElement={setSelectedElement}
                scrollViewRef={useRef<HTMLDivElement>(null)}
              />
            </div>
          </div>
        )}
      </div>
    </>
  );
}
