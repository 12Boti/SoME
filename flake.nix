{
  inputs = {
    # nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.05";
    flake-utils.url = "github:numtide/flake-utils";
    devshell.url = "github:numtide/devshell";
    mach-nix = {
      url = "github:DavHau/mach-nix";
      inputs.pypi-deps-db.follows = "pypi-deps-db";
    };
    pypi-deps-db = {
      url = "github:DavHau/pypi-deps-db";
      flake = false;
    };
  };

  outputs =
    { self
    , nixpkgs
    , flake-utils
    , mach-nix
    , devshell
    , pypi-deps-db
    }:
    flake-utils.lib.eachSystem [ "x86_64-linux" ] (system:
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
          setuptools
        '';
        _.click-default-group.src = pkgs.fetchFromGitHub {
          owner = "click-contrib";
          repo = "click-default-group";
          rev = "v1.2.2";
          hash = "sha256-Bmk9F3V/zGj0jReqHvvOuX9s1IDEGbwn4ggIOytNY1o=";
        };
      };
      convexityFont = pkgs.fetchzip {
        url = "https://www.1001fonts.com/download/new-rocker.zip";
        hash = "sha256-Zl36iQuJnSrEjxPaKF81nxMDWotbu11ehOFKDH7BLh4=";
        stripRoot = false;
      };
    in
    {
      packages.default = pkgs.stdenvNoCC.mkDerivation {
        name = "SoME.mp4";
        src = ./src;
        nativeBuildInputs = [
          python
          pkgs.ffmpeg
          pkgs.texlive.combined.scheme-full
        ];
        installPhase = ''
          scene=CreateConcavePolygon
          mkdir -p assets/font
          cp ${convexityFont}/NewRocker-Regular.ttf assets/font
          manim render main.py $scene
          mv media/videos/main/1080p60/$scene.mp4 $out
        '';
      };
    });
}
