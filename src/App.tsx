import Game from './components/Game.tsx';

import { ToastContainer } from 'react-toastify';
import { useState } from 'react';
import ReactModal from 'react-modal';

export default function Home() {
  const [helpModalOpen, setHelpModalOpen] = useState(false);
  return (
    <main className="relative flex h-screen w-screen flex-col font-body overflow-hidden bg-black">
      <ReactModal
        isOpen={helpModalOpen}
        onRequestClose={() => setHelpModalOpen(false)}
        style={modalStyles}
        contentLabel="Help modal"
        ariaHideApp={false}
      >
        <div className="font-body">
          <h1 className="text-center text-6xl font-bold font-display game-title">QuantumHive Town</h1>
          <p>
            Tu equipo de agentes AI en un mundo pixel art.
          </p>
          <h2 className="text-4xl mt-4">Interactuar</h2>
          <p>
            Hacé click en un agente para ver su info. El botón "Interact" te permite unirte al mundo y hablarles.
          </p>
          <h2 className="text-4xl mt-4">Navegar</h2>
          <p>
            Click y drag para moverte. Scroll para zoom.
          </p>
        </div>
      </ReactModal>

      <Game
        helpModalOpen={helpModalOpen}
        setHelpModalOpen={setHelpModalOpen}
      />

      <ToastContainer position="bottom-right" autoClose={2000} closeOnClick theme="dark" />
    </main>
  );
}

const modalStyles = {
  overlay: {
    backgroundColor: 'rgb(0, 0, 0, 85%)',
    zIndex: 12,
  },
  content: {
    top: '50%',
    left: '50%',
    right: 'auto',
    bottom: 'auto',
    marginRight: '-50%',
    transform: 'translate(-50%, -50%)',
    maxWidth: '50%',
    border: '10px solid rgb(23, 20, 33)',
    borderRadius: '0',
    background: 'rgb(35, 38, 58)',
    color: 'white',
    fontFamily: '"VCR OSD Mono", monospace',
  },
};
