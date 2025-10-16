import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { NotificationService } from '../../../services/notification.service';

@Component({
  selector: 'app-edit-gc',
  standalone: true,
  imports: [CommonModule, FormsModule, NavBarComponent, FooterComponent],
  templateUrl: './edit-gc.component.html',
  styleUrls: ['./edit-gc.component.css']
})
export class EditGcComponent implements OnInit {
  // Propriedades do formulário
  giftCardId: string | null = null;
  titulo: string = '';
  descricao: string = '';
  quantidade: number = 1;
  gerarCodigo: boolean = true;
  codigosManuais: string = '';
  valorSelecionado: number | null = null;
  valoresDisponiveis: number[] = [10, 25, 50, 75, 100, 150];
  
  imageSrc: string | null = null;
  selectedFile: File | null = null;
  isLoading: boolean = true;
  isUploading: boolean = false;

  // --- NOVOS CAMPOS ADICIONADOS ---
  ativo: boolean = true;
  validade: string = ''; // Formato yyyy-MM-dd para o input date
  nota: number | null = null;

  constructor(
    private giftcardService: GiftcardService,
    private route: ActivatedRoute,
    private router: Router,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.giftCardId = this.route.snapshot.paramMap.get('id');
    if (this.giftCardId) {
      this.giftcardService.getGiftCardById(this.giftCardId).subscribe({
        next: (data) => {
          // Preenche todos os campos com os dados existentes
          this.titulo = data.title;
          this.descricao = data.description;
          this.quantidade = data.quantityavailable;
          this.valorSelecionado = data.valor;
          this.gerarCodigo = data.generaterandomly;
          this.codigosManuais = data.codes || '';
          
          // --- PREENCHENDO OS NOVOS CAMPOS ---
          this.ativo = data.ativo;
          // Formata a data para o input (se existir)
          this.validade = data.validade ? new Date(data.validade).toISOString().split('T')[0] : '';
          this.nota = data.nota;
          
          if (data.imageUrl) {
            this.imageSrc = `http://127.0.0.1:8000/uploads/${data.imageUrl}`;
          }
          
          this.isLoading = false;
        },
        error: (err) => {
          console.error("Erro ao carregar dados para edição:", err);
          this.notificationService.show("Não foi possível carregar o Gift Card.", "error");
          this.router.navigate(['/dashboard-gc']);
        }
      });
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        this.imageSrc = reader.result as string;
      };
      reader.readAsDataURL(this.selectedFile);
    }
  }

  toggleGerarCodigo() { 
    this.gerarCodigo = !this.gerarCodigo;
    if (!this.gerarCodigo) {
      this.atualizarQuantidadePelosCodigos();
    }
  }

  atualizarQuantidadePelosCodigos(): void { 
    if (this.gerarCodigo) return;
    const codigos = this.codigosManuais?.split(';').filter(c => c.trim() !== '') || [];
    this.quantidade = codigos.length;
  }

  onSubmit(): void {
    if (!this.giftCardId) return;

    if (!this.gerarCodigo) {
        this.atualizarQuantidadePelosCodigos();
    }

    if (!this.titulo || this.quantidade < 1 || this.valorSelecionado === null) {
      this.notificationService.show('Por favor, preencha todos os campos obrigatórios.', "warning");
      return;
    }

    this.isUploading = true; // <-- ATIVA O CARREGAMENTO AQUI

    const formData = new FormData();
    formData.append('title', this.titulo);
    formData.append('valor', this.valorSelecionado.toString());
    formData.append('description', this.descricao);
    formData.append('quantityavailable', this.quantidade.toString());
    formData.append('generaterandomly', String(this.gerarCodigo));
    formData.append('ativo', String(this.ativo));
    if (this.validade) {
      formData.append('validade', this.validade);
    }
    if (this.nota !== null) {
      formData.append('nota', this.nota.toString());
    }
    if (!this.gerarCodigo) {
      const validCodes = this.codigosManuais.split(';').filter(c => c.trim() !== '').join(';');
      formData.append('codes', validCodes);
    }
    if (this.selectedFile) {
      formData.append('image', this.selectedFile, this.selectedFile.name);
    }

    this.giftcardService.updateGiftCard(this.giftCardId, formData).subscribe({
      next: () => {
        this.notificationService.show('Gift Card atualizado com sucesso!', "success");
        this.router.navigate(['/dashboard-gc']);
        this.isUploading = false; // <-- DESATIVA O CARREGAMENTO NO SUCESSO
      },
      error: (err) => {
        // --- LÓGICA DE ERRO ATUALIZADA ---
        const errorMessage = err.error?.detail || "Ocorreu um erro ao atualizar o Gift Card.";
        this.notificationService.show(errorMessage, "error");
        this.isUploading = false; // <-- DESATIVA O CARREGAMENTO NO ERRO
      }
    });
  }
}