from django import forms
from usuarios.models import PerfilUsuario


class QuestionarioPerfil(forms.Form):
    """Formulário para o questionário de perfil de investidor"""
    
    CHOICES_PERGUNTA_1 = [
        ('A', 'Preservar o capital, mesmo que o retorno seja baixo.'),
        ('B', 'Obter retornos moderados, aceitando riscos controlados.'),
        ('C', 'Maximizar o retorno, mesmo que isso implique em riscos elevados.'),
    ]
    
    CHOICES_PERGUNTA_2 = [
        ('A', 'Ficaria muito preocupado e resgataria parte ou todo o investimento.'),
        ('B', 'Ficaria apreensivo, mas manteria a calma e aguardaria a recuperação.'),
        ('C', 'Veria como uma oportunidade para comprar mais ativos a preços baixos.'),
    ]
    
    CHOICES_PERGUNTA_3 = [
        ('A', 'Básico: Conheço apenas os investimentos mais simples, como poupança.'),
        ('B', 'Médio: Conheço alguns tipos de investimentos e seus riscos.'),
        ('C', 'Avançado: Tenho bom conhecimento sobre diversos produtos e estratégias de investimento.'),
    ]
    
    CHOICES_PERGUNTA_4 = [
        ('A', 'Curto prazo (até 1 ano).'),
        ('B', 'Médio prazo (de 1 a 5 anos).'),
        ('C', 'Longo prazo (acima de 5 anos).'),
    ]
    
    CHOICES_PERGUNTA_5 = [
        ('A', 'Até 10%.'),
        ('B', 'Entre 10% e 30%.'),
        ('C', 'Acima de 30%.'),
    ]
    
    CHOICES_PERGUNTA_6 = [
        ('A', 'Não, prefiro investimentos com garantia de capital.'),
        ('B', 'Talvez, em uma pequena parte do meu capital.'),
        ('C', 'Sim, estou disposto a assumir esse risco em busca de maior rentabilidade.'),
    ]
    
    CHOICES_PERGUNTA_7 = [
        ('A', 'Concentrar em poucos investimentos seguros.'),
        ('B', 'Diversificar em diferentes classes de ativos, com foco em equilíbrio.'),
        ('C', 'Diversificar amplamente, incluindo ativos de maior risco para potencializar ganhos.'),
    ]
    
    CHOICES_PERGUNTA_8 = [
        ('A', 'Muito importante, preciso ter acesso ao dinheiro a qualquer momento.'),
        ('B', 'Importância moderada, posso esperar um pouco para resgatar.'),
        ('C', 'Pouco importante, priorizo o retorno a longo prazo.'),
    ]
    
    CHOICES_PERGUNTA_9 = [
        ('A', 'Raramente ou nunca.'),
        ('B', 'Ocasionalmente, quando há notícias relevantes.'),
        ('C', 'Constantemente, acompanho o mercado e faço ajustes quando necessário.'),
    ]
    
    CHOICES_PERGUNTA_10 = [
        ('A', 'Aplicação de baixo risco e retorno previsível (ex: CDB, Tesouro Direto Selic).'),
        ('B', 'Aplicação de risco moderado com potencial de retorno maior (ex: fundos multimercado, ações de empresas consolidadas).'),
        ('C', 'Aplicação de alto risco com grande potencial de retorno (ex: ações de empresas em crescimento, criptomoedas).'),
    ]
    
    pergunta_1 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_1,
        widget=forms.RadioSelect,
        label='1. Qual o seu principal objetivo ao investir?',
        required=True
    )
    
    pergunta_2 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_2,
        widget=forms.RadioSelect,
        label='2. Como você reagiria a uma queda de 20% no valor dos seus investimentos em um curto período?',
        required=True
    )
    
    pergunta_3 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_3,
        widget=forms.RadioSelect,
        label='3. Qual o seu conhecimento sobre o mercado financeiro e os produtos de investimento?',
        required=True
    )
    
    pergunta_4 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_4,
        widget=forms.RadioSelect,
        label='4. Por quanto tempo você pretende manter seus investimentos?',
        required=True
    )
    
    pergunta_5 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_5,
        widget=forms.RadioSelect,
        label='5. Qual a porcentagem da sua renda mensal você está disposto a destinar para investimentos?',
        required=True
    )
    
    pergunta_6 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_6,
        widget=forms.RadioSelect,
        label='6. Você se sentiria confortável em investir em produtos que não garantem o capital principal, mas que podem oferecer retornos mais altos?',
        required=True
    )
    
    pergunta_7 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_7,
        widget=forms.RadioSelect,
        label='7. Em relação à diversificação, qual sua preferência?',
        required=True
    )
    
    pergunta_8 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_8,
        widget=forms.RadioSelect,
        label='8. Qual a importância da liquidez (facilidade de resgatar o dinheiro) para você?',
        required=True
    )
    
    pergunta_9 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_9,
        widget=forms.RadioSelect,
        label='9. Você costuma acompanhar de perto o desempenho dos seus investimentos?',
        required=True
    )
    
    pergunta_10 = forms.ChoiceField(
        choices=CHOICES_PERGUNTA_10,
        widget=forms.RadioSelect,
        label='10. Se você tivesse um valor extra para investir hoje, qual seria sua escolha?',
        required=True
    )
    
    def calcular_perfil(self):
        """Calcula o perfil do investidor baseado nas respostas"""
        if not self.is_valid():
            return None
        
        pontuacao = {'A': 0, 'B': 0, 'C': 0}
        
        for i in range(1, 11):
            resposta = self.cleaned_data.get(f'pergunta_{i}')
            if resposta:
                pontuacao[resposta] += 1
        
        # Determina o perfil baseado na resposta mais frequente
        if pontuacao['A'] >= pontuacao['B'] and pontuacao['A'] >= pontuacao['C']:
            return 'conservador'
        elif pontuacao['C'] >= pontuacao['B']:
            return 'agressivo'
        else:
            return 'moderado'


class StockSelectionForm(forms.Form):
    """Formulário para seleção de ações"""
    STOCK_CHOICES = [
        ('AAPL', 'Apple (AAPL)'),
        ('MSFT', 'Microsoft (MSFT)'),
        ('TSLA', 'Tesla (TSLA)'),
        ('GOOG', 'Alphabet (GOOG)'),
        ('AMZN', 'Amazon (AMZN)'),
        ('META', 'Meta (META)'),
        ('NFLX', 'Netflix (NFLX)'),
        ('NVDA', 'Nvidia (NVDA)'),
        ('BRK.B', 'Berkshire Hathaway (BRK.B)'),
        ('JPM', 'JPMorgan Chase (JPM)'),
        ('V', 'Visa (V)'),
        ('DIS', 'Disney (DIS)'),
        ('PYPL', 'PayPal (PYPL)'),
        ('INTC', 'Intel (INTC)'),
        ('ADBE', 'Adobe (ADBE)'),
        ('ORCL', 'Oracle (ORCL)'),
        ('CSCO', 'Cisco (CSCO)'),
        ('PEP', 'PepsiCo (PEP)'),
        ('KO', 'Coca-Cola (KO)'),
        ('MCD', "McDonald's (MCD)"),
    ]
    
    stocks = forms.MultipleChoiceField(
        choices=STOCK_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Selecione até 3 ações'
    )
    
    def clean_stocks(self):
        """Valida que no máximo 3 ações foram selecionadas"""
        stocks = self.cleaned_data.get('stocks', [])
        if len(stocks) > 3:
            raise forms.ValidationError('Selecione no máximo 3 ações.')
        return stocks
