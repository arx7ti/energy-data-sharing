with import <nixpkgs> {};
let
  unstable = import <unstable> {};
  wtforms_stable = pkgs.python37.pkgs.buildPythonPackage rec {
    pname = "WTForms";
    version = "2.3.3";
    src = pkgs.fetchFromGitHub {
      owner  = "wtforms";
      repo   = "wtforms";
      rev    = "244c8d6b15accb3e2efd622241e5f7c1cc8abb9d";
      sha256 = "0aix0655k8cbylpxi6lgyakigg51iy6bhj248g7d26d0mcpwl6mi";
    };
    doCheck = false;
    propagatedBuildInputs = with pkgs.python37Packages; [
      markupsafe
    ];
  };
  flask_wtf_stable = pkgs.python37.pkgs.buildPythonPackage rec {
    pname = "Flask-WTF";
    version = "0.14.3";
    src = pkgs.fetchFromGitHub {
      owner  = "lepture";
      repo   = "flask-wtf";
      rev    = "dc786301c5b6c10a8b1b256d9820c8a7a932d99c";
      sha256 = "1qnda06f4lq453n5wzl430ywm2fqkppc2zgiw53z8k36jzhvb6xk";
    };
    doCheck = false;
    propagatedBuildInputs = with pkgs.python37Packages; [
      wtforms_stable
      itsdangerous
      flask
    ];
  };
in
  stdenv.mkDerivation rec {
    name = "development";
    dependencies = (with pkgs; [
      python3
    ]) ++ (with python37Packages; [
      black
      requests
      psycopg2
      flask
      flask-bootstrap
      flask-restful
      flask_migrate
      flask-pymongo
      flask_script
      flask_mail
      flask_login
      flask_sqlalchemy
      flask_wtf_stable
    ]);
    env = buildEnv {
      name = name;
      paths = dependencies;
    };
    buildInputs = dependencies;
    FLASK_APP = "application.py";
    FLASK_ENV = name;
    FLASK_DEBUG = 1;
}
