{
  description = "Python development environment for easy-prompt";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      # List of supported systems, including Apple Silicon, Intel Mac, and Linux.
      supportedSystems = [ "aarch64-darwin" "x86_64-darwin" "x86_64-linux" ];

      # Helper function to generate a dev shell for a given system.
      mkDevShell = system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonVersion = pkgs.python311;
        in
        pkgs.mkShell {
          # The 'buildInputs' are the packages that will be available in your shell.
          buildInputs = [
            # Python itself
            pythonVersion

            # Utility to manage virtual environments
            pkgs.python311Packages.virtualenv

            # For direnv integration
            pkgs.direnv
            pkgs.nix-direnv

            # Node.js was removed as it was causing errors.
          ];

          # This hook provides a welcome message. The actual venv creation
          # is now handled by the 'layout python' command in .envrc.
          shellHook = ''
            echo "Welcome to the easy-prompt dev environment!"
            echo "Nix has prepared Python for you."
            echo "The Python virtual environment is managed by direnv."
          '';
        };
    in
    {
      # Create a devShell for each supported system.
      devShells = nixpkgs.lib.genAttrs supportedSystems (system: {
        default = mkDevShell system;
      });
    };
}
