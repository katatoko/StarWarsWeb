using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using StarWarsWeb.Client.Utils;

var builder = WebAssemblyHostBuilder.CreateDefault(args);

// Registra el HttpClient apuntando a la api
// no es necesario usar CorrelationId porque solo tenemos una api
builder.Services.AddScoped(sp => new HttpClient
{
    BaseAddress = new Uri("https://localhost:7155/")
});

// registra el gestor para mantener la sesion del usuario en memoria del cliente
builder.Services.AddScoped<UserState>();

await builder.Build().RunAsync();
