namespace StarWarsWeb.Client.Utils
{
    // Gestor de estado de sesion, para que mantenga en memoria del navegador
    // los datos del usuario autenticado
    // bloquea la ruta del catalogo de personajes sin haberse autenticado
    public class UserState
    {
        public bool IsAuthenticated { get; private set; }
        public string? FullName { get; private set; }
        public string? Email { get; private set; }

        // reactividad, cambia dinamicamente cuando incia sesion
        public event Action? OnChange;

        public void SetUser(string fullName, string email)
        {
            IsAuthenticated = true;
            FullName = fullName;
            Email = email;
            OnChange?.Invoke();
        }

        public void Logout()
        {
            IsAuthenticated = false;
            FullName = null;
            Email = null;
            OnChange?.Invoke();
        }
    }
}
