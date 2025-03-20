use serde::{Deserialize, Serialize};
use bcrypt::{hash, DEFAULT_COST};
use jsonwebtoken::{encode, EncodingKey, Header};
use std::env;
use dotenv::dotenv;
use std::time::{SystemTime, UNIX_EPOCH};
use actix_web::{web, HttpResponse, Responder, App, HttpServer};
use firebase::{Client, credentials::{Credentials, ServiceAccount}};
use std::env;
use std::fs::File;
use std::io::Read;

#[derive(Deserialize)]
pub struct RegisterUser {
    pub email: String,
    pub username: String,
    pub password: String,
}

fn hash_password(password: &str) -> Result<String, bcrypt::BcryptError> {
    hash(password, DEFAULT_COST)
}

#[derive(Serialize, Deserialize)]
struct Claims {
    sub: String, 
    exp: usize,   
}

pub async fn register_user(user: web::Json<RegisterUser>) -> impl Responder {
    let hashed_password = match hash_password(&user.password) {
        Ok(h) => h,
        Err(_) => return HttpResponse::InternalServerError().finish(),
    };

    let db: Database = client.database("https://bd-giftcard-default-rtdb.firebaseio.com/");  

    
    let ref_users: Reference = db.reference("users");

    
    ref_users.push(user).expect("Erro ao salvar dados no Firebase");

    
    match generate_jwt(&user.email) {
        Ok(token) => HttpResponse::Ok().json(TokenResponse { token }),
        Err(_) => HttpResponse::InternalServerError().finish(),
    }
}


fn generate_jwt(email: &str) -> Result<String, jsonwebtoken::errors::Error> {
    dotenv().ok(); 
    let secret = env::var("JWT_SECRET").expect("JWT_SECRET não definido");

    let expiration = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs() + 86400; 

    let claims = Claims {
        sub: email.to_owned(),
        exp: expiration as usize,
    };

    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_ref()),
    )
}

fn initialize_firebase() -> Client {
    
    let service_account_file = env::var("FIREBASE_SERVICE_ACCOUNT_FILE").expect("FIREBASE_SERVICE_ACCOUNT_FILE não definido");

    let mut file = File::open(service_account_file).expect("Arquivo de credenciais não encontrado");
    let mut json_data = String::new();
    file.read_to_string(&mut json_data).expect("Falha ao ler o arquivo de credenciais");

    
    let credentials = Credentials::from_service_account_json(&json_data).expect("Falha ao carregar credenciais");
    
    
    let firebase_client = Client::new(credentials);
    firebase_client
}



#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .route("/register", web::post().to(register_user))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}