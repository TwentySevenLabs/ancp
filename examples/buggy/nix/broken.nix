{ pkgs }:

pkgs.mkShell {
  packages = [
    pkgs.git
  ;
}
