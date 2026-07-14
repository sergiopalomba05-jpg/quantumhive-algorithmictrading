#!/usr/bin/env python3
"""
Exporta un modelo PPO entrenado a ONNX (opset 11).

Uso:
    python scripts/exportar_onnx.py modelos/modelo_final.zip onnx/bot_unificado.onnx
"""
import argparse
import sys
from pathlib import Path

try:
    import torch
    from stable_baselines3 import PPO
except ImportError:
    print("ERROR: stable-baselines3 y torch requeridos.")
    print("  pip install stable-baselines3 torch")
    sys.exit(1)


class ActorNet(torch.nn.Module):
    """Wrapper que expone solo la red actor de SB3 PPO para ONNX export."""

    def __init__(self, policy):
        super().__init__()
        self.mlp_extractor = policy.mlp_extractor
        self.action_net = policy.action_net

    def forward(self, observations: torch.Tensor):
        latent_pi, _ = self.mlp_extractor(observations)
        return self.action_net(latent_pi)


def export(model_path: Path, onnx_path: Path):
    print(f"[EXPORT] Cargando {model_path}...")
    model = PPO.load(model_path)

    obs_shape = model.policy.observation_space.shape[0]
    dummy_input = torch.randn(1, obs_shape)
    print(f"[EXPORT] Dummy input shape: {dummy_input.shape} | obs={obs_shape}")

    actor = ActorNet(model.policy)
    actor.eval()

    onnx_path.parent.mkdir(parents=True, exist_ok=True)

    torch.onnx.export(
        actor,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["observations"],
        output_names=["action_logits"],
        dynamic_axes={"observations": {0: "batch_size"}, "action_logits": {0: "batch_size"}},
    )
    print(f"[EXPORT] Guardado: {onnx_path}")


def main():
    parser = argparse.ArgumentParser(description="Exportar PPO a ONNX")
    parser.add_argument("model", type=Path, help="Ruta a modelo_final.zip")
    parser.add_argument("onnx", type=Path, help="Ruta de salida .onnx")
    args = parser.parse_args()

    if not args.model.exists():
        print(f"ERROR: Modelo no encontrado: {args.model}")
        sys.exit(1)

    export(args.model, args.onnx)
    print("✅ Export completado.")


if __name__ == "__main__":
    main()
