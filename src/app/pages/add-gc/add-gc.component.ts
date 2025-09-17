import { Component } from '@angular/core';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { GiftcardService } from '../../../services/giftcard.service';
import { Router, RouterLink } from '@angular/router';
import { NotificationService } from '../../../services/notification.service';

@Component({
  selector: 'app-add-gc',
  standalone: true,
  imports: [NavBarComponent, FooterComponent, FormsModule, CommonModule, RouterLink],
  templateUrl: './add-gc.component.html',
  styleUrl: './add-gc.component.css'
})
export class AddGcComponent {
  titulo: string = '';
  descricao: string = '';
  quantidade: number = 1;
  gerarCodigo: boolean = true;
  codigosManuais: string = '';
  valorSelecionado: number | null = null;
  valoresDisponiveis: number[] = [10, 25, 50, 75, 100, 150];
  imageSrc: string | null = null;
  selectedFile: File | null = null;

  // --- NOVOS CAMPOS ADICIONADOS ---
  ativo: boolean = true;
  validade: string = ''; // Usar string para o formato yyyy-MM-dd do input date
  nota: number | null = null;

  constructor(
    private giftcardService: GiftcardService,
    private router: Router,
    private notificationService: NotificationService
  ) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      this.selectedFile = null;
      this.imageSrc = null;
      return;
    }
    this.selectedFile = input.files[0];
    const reader = new FileReader();
    reader.onload = () => {
      this.imageSrc = reader.result as string;
    };
    reader.readAsDataURL(this.selectedFile);
  }

  toggleGerarCodigo() {
    this.gerarCodigo = !this.gerarCodigo;
    if (!this.gerarCodigo) {
      this.atualizarQuantidadePelosCodigos();
    }
  }

  atualizarQuantidadePelosCodigos(): void {
    if (this.gerarCodigo) return;
    if (!this.codigosManuais || this.codigosManuais.trim() === '') {
      this.quantidade = 0;
      return;
    }
    const codigos = this.codigosManuais.split(';').filter(codigo => codigo.trim() !== '');
    this.quantidade = codigos.length;
  }
  
  onSubmit(): void {
    if (!this.gerarCodigo) {
        this.atualizarQuantidadePelosCodigos();
    }

    if (!this.titulo || this.quantidade < 1 || this.valorSelecionado === null) {
      this.notificationService.show(
        'Por favor, preencha título, selecione um valor e informe ao menos um código ou quantidade válida.',
        'warning'
      );
      return;
    }

    const formData = new FormData();

    formData.append('title', this.titulo);
    formData.append('valor', this.valorSelecionado.toString());
    formData.append('description', this.descricao);
    formData.append('quantityavailable', this.quantidade.toString());
    formData.append('generaterandomly', String(this.gerarCodigo));

    // --- ENVIANDO OS NOVOS CAMPOS PARA A API ---
    formData.append('ativo', String(this.ativo));
    if (this.validade) {
      formData.append('validade', this.validade);
    }
    if (this.nota !== null) {
      formData.append('nota', this.nota.toString());
    }
    
    if (!this.gerarCodigo) {
      const validCodes = this.codigosManuais.split(';').filter(codigo => codigo.trim() !== '').join(';');
      formData.append('codes', validCodes);
    }

    if (this.selectedFile) {
      formData.append('image', this.selectedFile, this.selectedFile.name);
    }

    this.giftcardService.createGiftCard(formData).subscribe({
      next: () => {
        this.notificationService.show('Gift Card cadastrado com sucesso!', 'success');
        // Limpar o formulário
        this.titulo = '';
        this.descricao = '';
        this.quantidade = 1;
        this.valorSelecionado = null;
        this.gerarCodigo = true;
        this.codigosManuais = '';
        this.imageSrc = null;
        this.selectedFile = null;
        this.ativo = true;
        this.validade = '';
        this.nota = null;
        this.router.navigate(['/dashboard-gc']);
      },
      error: (error) => {
        this.notificationService.show('Ocorreu um erro ao cadastrar o Gift Card. Verifique se está logado.', 'error');
        console.error('Erro ao criar Gift Card:', error);
      }
    });
  }
}
