{
  inputs = {
    # nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix.url = "github:DavHau/mach-nix";
    devshell.url = "github:numtide/devshell";
  };

  outputs =
    { self
    , nixpkgs
    , flake-utils
    , mach-nix
    , devshell
    }:
    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
      inherit (devshell.legacyPackages.${system}) mkShell;
      inherit (mach-nix.lib.${system}) mkPython;
      python = mkPython {
        python = "python310";
        requirements = ''
          manim
          matplotlib
          mypy
          shed
        '';
        _.click-default-group.src = pkgs.fetchFromGitHub {
          owner = "click-contrib";
          repo = "click-default-group";
          rev = "v1.2.2";
          hash = "sha256-Bmk9F3V/zGj0jReqHvvOuX9s1IDEGbwn4ggIOytNY1o=";
        };
      };
    in
    {
      packages.default = pkgs.stdenvNoCC.mkDerivation {
        name = "SoME.mp4";
        src = ./src;
        nativeBuildInputs = [
          python
          pkgs.ffmpeg
        ];
        installPhase = ''
          scene=CreateConcavePolygon
          manim render main.py $scene
          mv media/videos/main/1080p60/$scene.mp4 $out
        '';
      };
    });
}
