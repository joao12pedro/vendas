/**
 * Classe para gerenciar a autenticação
 */
class Auth {
  /**
   * Verifica se o usuário está logado
   * @returns {boolean} - true se estiver logado, false caso contrário
   */
  static isLoggedIn() {
    return localStorage.getItem("usuario") !== null
  }

  /**
   * Obtém os dados do usuário logado
   * @returns {object|null} - Dados do usuário ou null se não estiver logado
   */
  static getUsuario() {
    const usuario = localStorage.getItem("usuario")
    return usuario ? JSON.parse(usuario) : null
  }

  /**
   * Realiza o login do usuário
   * @param {object} usuario - Dados do usuário
   */
  static login(usuario) {
    localStorage.setItem("usuario", JSON.stringify(usuario))
  }

  /**
   * Realiza o logout do usuário
   */
  static logout() {
    localStorage.removeItem("usuario")
  }
}
