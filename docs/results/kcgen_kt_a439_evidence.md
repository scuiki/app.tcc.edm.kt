# Os trechos dos conceitos no A439

Para cada problema do A439 da extração de referência, cujo resultado está em
[kcgen_kt_a439_reference_extraction.md](kcgen_kt_a439_reference_extraction.md), a tabela liga cada
conceito ao trecho que o LLM apontou numa das cinco soluções que ele leu, com a solução, as linhas e
o código do trecho. Depois da tabela vem o código completo das cinco soluções, na ordem em que elas
entraram no prompt, com o número de cada linha na frente para achar o trecho. As soluções são
execuções corretas de alunos da CSEDM, identificadas pelo `CodeStateID` do dataset.

O trecho é a justificativa que o modelo escreve, e não a causa da extração. Um conceito sem trecho é
um conceito em que o LLM apontou um código que não está na solução, e o app o descartou.


## Problema 1, `sortaSum`

> Write a function in Java that implements the following logic: Given 2 ints, a and b, return their sum. However, sums in the range 10..19 inclusive, are forbidden, so in that case just return 20.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Operações aritméticas básicas | 2 | 3 | `int sum = a + b;` |
| Estruturas de instrução if-else | 1 | 3 a 5 | `if (a + b >= 10 && a + b <= 19)`<br>`return 20;`<br>`else return (a + b);` |
| Operadores lógicos e condicionais | 1 | 3 | `if (a + b >= 10 && a + b <= 19)` |
| Comparações numéricas | 1 | 3 | `if (a + b >= 10 && a + b <= 19)` |

### Solução 1, CodeStateID `1751105`

```java
1  public int sortaSum(int a, int b)
2  {
3      if (a + b >= 10 && a + b <= 19)
4          return 20;
5      else return (a + b);
6  }
```

### Solução 2, CodeStateID `1738251`

```java
 1  public int sortaSum(int a, int b)
 2  {
 3      int sum = a + b;
 4      
 5      if (sum == 10 || sum == 11 || sum == 12 || sum == 13 || sum == 14 || sum == 15 || sum == 16 || sum == 17 || sum == 18 || sum == 19) 
 6      {
 7          return 20;
 8      }
 9      return sum;
10  }
```

### Solução 3, CodeStateID `1720866`

```java
 1  public int sortaSum(int a, int b) {
 2  
 3  int sum = 0;
 4  
 5  sum = a + b;
 6  
 7  if(sum >=10 && sum <=19) {
 8  
 9  sum = 20;
10  
11  }
12  
13  return sum;
14  
15  }
```

### Solução 4, CodeStateID `1751006`

```java
1  public int sortaSum(int a, int b) {
2  		int sum = a + b;		
3  		return sum >= 10 && sum < 20 ? 20 : sum;
4  	}
```

### Solução 5, CodeStateID `1750685`

```java
 1  public int sortaSum(int a, int b)
 2  {
 3     if ( a + b >= 10 && a + b <= 19 )
 4     {
 5     return 20;
 6     }
 7    else 
 8    {
 9        return ( a + b );
10    }
11      
12  }
```

## Problema 3, `in1To10`

> Write a function in Java that implements the following logic: Given a number n, return true if n is in the range 1..10, inclusive. Unless "outsideMode" is true, in which case return true if the number is less or equal to 1, or greater or equal to 10.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Estruturas de instrução if-else | 2 | 5 a 12 | `if (n <= 1 \|\| n >= 10)`<br>`{`<br>`return true;`<br>`}`<br>`else`<br>`{`<br>`return false;`<br>`}` |
| Uso do tipo de dado boolean | 2 | 1 | `public boolean in1To10(int n, boolean outsideMode)` |
| Operadores lógicos e condicionais | 3 | 5 | `if ( outsideMode == true && ( n <= 1 \|\| n >= 10 ) )` |
| Comparações numéricas | 4 | 4 | `return (n <= 1 \|\| n >= 10);` |

### Solução 1, CodeStateID `1744380`

```java
 1  public boolean in1To10(int n, boolean outsideMode)
 2  {
 3      if(outsideMode)
 4          if(n<=1 || n>=10)
 5          {return true;}
 6      else
 7      {
 8          return false;}
 9      
10      if(n>=1 && n<=10)
11      {return true;   }
12      return false;
13      
14  }
```

### Solução 2, CodeStateID `1727024`

```java
 1  public boolean in1To10(int n, boolean outsideMode)
 2  {
 3      if (outsideMode)
 4      {
 5          if (n <= 1 || n >= 10)
 6          {
 7              return true;
 8          }
 9          else
10          {
11              return false;
12          }
13      }
14      else 
15      {
16          if (n >= 1 && n <= 10)
17          {
18              return true;
19          }
20          else 
21          {
22              return false;
23          }
24      }
25  }
```

### Solução 3, CodeStateID `1723228`

```java
1  public boolean in1To10(int n, boolean outsideMode)
2  {
3      if ( outsideMode == false && n >= 1 && n <= 10 )
4     return true;
5    if ( outsideMode == true && ( n <= 1 || n >= 10 ) )
6     return true;
7    else return false;
8  }
```

### Solução 4, CodeStateID `1738549`

```java
1  public boolean in1To10(int n, boolean outsideMode)
2  {
3      if (outsideMode)
4          return (n <= 1 || n >= 10);
5      return (n >= 1 && n <= 10);
6  }
```

### Solução 5, CodeStateID `1751097`

```java
1  public boolean in1To10(int n, boolean outsideMode) {
2  		if(outsideMode) {
3  			return n <= 1 || n >= 10;
4  		}
5  		return n >= 1 && n <= 10;
6  	}
```

## Problema 5, `answerCell`

> Write a function in Java that implements the following logic: Your cell phone rings. Return true if you should answer it. Normally you answer, except in the morning you only answer if it is your mom calling. In all cases, if you are asleep, you do not answer.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Inicialização e atribuição de variável | 1 | 3 | `boolean answer = true;` |
| Estruturas de instrução if-else | 2 | 3 a 8 | `if (isAsleep)`<br>`return false;`<br>`else if (!isMorning \|\| isMom)`<br>`return true;`<br>`else`<br>`return false;` |
| Instrução de retorno | 1 | 16 | `return answer;` |
| Operadores lógicos e condicionais | 1 | 10 | `else if (isMorning && !isMom && !isAsleep)` |

### Solução 1, CodeStateID `1727816`

```java
 1  public boolean answerCell(boolean isMorning, boolean isMom, boolean isAsleep)
 2  {
 3      boolean answer = true;
 4          
 5      if (isAsleep)
 6      {
 7         answer = false;
 8      }
 9      
10      else if (isMorning && !isMom && !isAsleep)
11      {
12       	answer = false;   
13      }
14  
15      
16      return answer;
17  }
```

### Solução 2, CodeStateID `1720489`

```java
1  public boolean answerCell(boolean isMorning, boolean isMom, boolean isAsleep)
2  {
3      if (isAsleep)
4          return false;
5      else if (!isMorning || isMom)
6          return true;
7      else
8          return false;
9  }
```

### Solução 3, CodeStateID `1741257`

```java
1  public boolean answerCell(boolean isMorning, boolean isMom, boolean isAsleep)
2  {
3      if(isAsleep)
4  		return false;
5  	if(isMom)
6  		return true;
7  	return (!isMorning);
8  }
```

### Solução 4, CodeStateID `1729338`

```java
 1  public boolean answerCell(boolean isMorning, boolean isMom, boolean isAsleep)
 2  {
 3      if (isAsleep)
 4      {
 5          return false;
 6      }
 7      else
 8      {
 9          if (isMom)
10          {
11              return true;
12          }
13          else
14          {
15              if (isMorning)
16              {
17                  return false;
18              }
19              else
20              {
21                  return true;
22              }
23          }
24      }
25  }
```

### Solução 5, CodeStateID `1729351`

```java
 1  public boolean answerCell(boolean isMorning, boolean isMom, boolean isAsleep)
 2  {
 3      if (isAsleep)
 4      {
 5          return false;
 6      }
 7      else if (isMorning)
 8      {
 9          if (isMom)
10          {
11              return true;
12          }
13          else
14          {
15              return false;
16          }
17      }
18      else
19      {
20          return true;
21      }
22  }
```

## Problema 12, `squirrelPlay`

> Write a function in Java that implements the following logic: The squirrels in Palo Alto spend most of the day playing. In particular, they play if the temperature is between 60 and 90 (inclusive). Unless it is summer, then the upper limit is 100 instead of 90. Given an int temperature and a boolean isSummer, return true if the squirrels play and false otherwise.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Inicialização e atribuição de variável | 5 | 3 a 4 | `int max = 90;`<br>`if(isSummer)max=100;` |
| Estruturas de instrução if-else | 1 | 5 a 12 | `if (temp >= 60 && temp <= 100)`<br>`{`<br>`return (true);`<br>`}`<br>`else`<br>`{`<br>`return (false);`<br>`}` |
| Operadores lógicos e condicionais | 3 | 3 | `if((temp>=60 && temp<=90) && !isSummer)` |
| Comparações numéricas | 4 | 4 | `return temp >= 60 && temp <= upperLimit;` |

### Solução 1, CodeStateID `1741451`

```java
 1  public boolean squirrelPlay(int temp, boolean isSummer)
 2  {
 3      if (isSummer)
 4      {
 5      	if (temp >= 60 && temp <= 100)
 6          {
 7          	return (true);
 8          }
 9          else
10          {
11          	return (false);
12          }
13      }
14      else
15      {
16      	if (temp >= 60 && temp <= 90)
17          {
18          	return (true);
19          }
20          else
21          {
22          	return (false);
23          }
24      }
25  }
```

### Solução 2, CodeStateID `1720838`

```java
 1  public static boolean squirrelPlay(int a, boolean b)
 2  {
 3  int upper = 90;
 4  
 5  if(b)
 6  
 7  upper = 100;
 8  
 9  return (a>=60 && a<=upper);
10  }
```

### Solução 3, CodeStateID `1720056`

```java
 1  public boolean squirrelPlay(int temp, boolean isSummer)
 2  {
 3  	if((temp>=60 && temp<=90) && !isSummer)
 4      {
 5      	return true;
 6      }
 7      
 8      else if(isSummer == true)
 9      {
10      	if(temp>=60 && temp<=100)
11          {
12          	return true;
13          }
14      }
15      
16      return false;
17  }
```

### Solução 4, CodeStateID `1750979`

```java
1  public boolean squirrelPlay(int temp, boolean isSummer)
2  {
3  		int upperLimit = isSummer ? 100 : 90;
4  		return temp >= 60 && temp <= upperLimit;
5  	}
```

### Solução 5, CodeStateID `1734413`

```java
1  public boolean squirrelPlay(int temp, boolean isSummer)
2  {
3      int max = 90;
4      if(isSummer)max=100;
5      return(temp>=60&&temp<=max);
6  }
```

## Problema 13, `caughtSpeeding`

> Write a function in Java that implements the following logic: You are driving a little too fast, and a police officer stops you. Write code to compute the result, encoded as an int value: 0=no ticket, 1=small ticket, or 2=big ticket. If speed is 60 or less, the result is 0. If speed is between 61 and 80 inclusive, the result is 1. If speed is 81 or more, the result is 2. Unless it is your birthday--on that day, your speed can be 5 higher in all cases.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Operações aritméticas básicas | 4 | 3 | `if (isBirthday) speed -= 5;` |
| Estruturas de instrução if-else | 5 | 6 a 13 | `if(speed <= 60)`<br>`return 0;`<br>`else if(speed <= 80)`<br>`return 1;`<br>`else`<br>`return 2;` |
| Uso do tipo de dado boolean | 3 | 11 | `if (!isBirthday) {` |
| Operadores lógicos e condicionais | 4 | 5 | `return (speed > 60 && speed <= 80) ? 1 : 2;` |
| Comparações numéricas | 1 | 3 | `if ( speed > 65 && speed <= 85 && isBirthday == true )` |

### Solução 1, CodeStateID `1723208`

```java
 1  public int caughtSpeeding(int speed, boolean isBirthday)
 2  {
 3      if ( speed > 65 && speed <= 85 && isBirthday == true )
 4     return 1;
 5    if ( speed >= 86 && isBirthday == true )
 6     return 2;
 7    if ( speed <= 65 && isBirthday == true )
 8     return 0;
 9    if ( speed > 60 && speed <= 80 )
10     return 1;
11    if ( speed >= 81 )
12     return 2;
13    else
14     return 0;
15  }
```

### Solução 2, CodeStateID `1719957`

```java
 1  public int caughtSpeeding(int speed, boolean isBirthday)
 2  {
 3  	if (isBirthday)
 4      {
 5      	if (speed <= 65)
 6          {
 7              return 0;
 8          }
 9          else if (speed >= 66 && speed <=85)
10          {
11              return 1;
12          }
13          else
14          {
15              return 2;
16          }
17      }
18      else
19      {
20          if (speed <= 60)
21          {
22              return 0;
23          }
24          else if (speed >= 61 && speed <=80)
25          {
26              return 1;
27          }
28          else 
29          {
30              return 2;
31          }
32      }    
33  }
```

### Solução 3, CodeStateID `1720434`

```java
 1    public int caughtSpeeding(int speed, boolean isBirthday) {
 2         int resultTicket = 0;
 3         if (isBirthday) {
 4             if (speed <= 65)
 5                 resultTicket = 0;
 6             if (speed > 65 && speed <= 85)
 7                 resultTicket = 1;
 8             if (speed > 85)
 9                 resultTicket = 2;
10         }
11         if (!isBirthday) {
12             if (speed <= 60)
13                 resultTicket = 0;
14             if (speed > 60 && speed <= 80)
15                 resultTicket = 1;
16             if (speed > 80)
17                 resultTicket = 2;
18         }
19         return resultTicket;
20     }
```

### Solução 4, CodeStateID `1739458`

```java
1  public int caughtSpeeding(int speed, boolean isBirthday)
2  {
3      if (isBirthday) speed -= 5;
4      if (speed <= 60) return 0;
5      return (speed > 60 && speed <= 80) ? 1 : 2;
6  }
```

### Solução 5, CodeStateID `1733562`

```java
 1  public int caughtSpeeding(int speed, boolean isBirthday)
 2  {
 3      if(isBirthday)
 4  		speed -= 5;
 5      
 6  	if(speed <= 60)
 7  		return 0;
 8      
 9  	else if(speed <= 80)
10  		return 1;
11      
12  	else
13  		return 2;
14  }
```

## Problema 232, `alarmClock`

> Given a day of the week encoded as 0 = Sun, 1 = Mon, 2 = Tue, ... 6 = Sat, and a boolean indicating if we are on vacation, return a string of the form "7:00" indicating when the alarm clock should ring. Weekdays, the alarm should be "7:00" and on the weekend it should be "10:00". Unless we are on vacation--then on weekdays it should be "10:00" and weekends it should be "off".

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Estruturas de instrução if-else | 2 | 3 a 7 | `if(day == 0)`<br>`if(vacation)`<br>`return "off";`<br>`else`<br>`return "10:00";` |
| Uso do tipo de dado boolean | 2 | 9 a 10 | `if(vacation)`<br>`return "10:00";` |
| Operadores lógicos e condicionais | 1 | 3 | `if ( vacation == true && ( day == 0 \|\| day == 6 ) )` |
| Comparações numéricas | 4 | 5 | `if (day <= 5 && day >= 1)` |

### Solução 1, CodeStateID `1751054`

```java
 1  public String alarmClock(int day, boolean vacation)
 2  {
 3          if ( vacation == true && ( day == 0 || day == 6 ) )
 4     return "off";
 5    if ( vacation == true && ( day == 1 || day == 2 || day == 3 || day == 4 || day == 5 ) )
 6     return "10:00";
 7    if ( vacation == false && ( day == 0 || day == 6 ) )
 8     return "10:00";
 9    else return "7:00";
10  }
```

### Solução 2, CodeStateID `1729518`

```java
 1  public String alarmClock(int day, boolean vacation)
 2  {
 3      if(day == 0)
 4          if(vacation)
 5              return "off";
 6          else
 7              return "10:00";
 8      else if(day == 1)
 9          if(vacation)
10              return "10:00";
11      	else
12              return "7:00";
13      else if(day == 2)
14          if(vacation)
15              return "10:00";
16      	else
17              return "7:00";
18      else if(day == 3)
19          if(vacation)
20              return "10:00";
21      	else
22              return "7:00";
23      else if(day == 4)
24          if(vacation)
25              return "10:00";
26      	else
27              return "7:00";
28      else if(day == 5)
29          if(vacation)
30              return "10:00";
31      	else 
32              return "7:00";
33      else
34          if(vacation)
35              return "off";
36      	else
37              return "10:00";
38      
39      
40  }
```

### Solução 3, CodeStateID `1720577`

```java
 1  public String alarmClock(int a, boolean b)
 2  {
 3  
 4  String k = "7:00";
 5  
 6  String c = "10:00";
 7  
 8  if(b)
 9  
10  {
11  
12  k = "10:00";
13  
14  c = "off";
15  
16  }
17  
18  if(a>0 && a<6)
19  
20  return k;
21  
22  else
23  
24  return c;
25  
26  }
```

### Solução 4, CodeStateID `1735124`

```java
 1  public String alarmClock(int day, boolean vacation)
 2  {
 3      if (vacation)
 4      {
 5          if (day <= 5 && day >= 1)
 6          {
 7              return "10:00";
 8          }
 9          else
10          {
11              return "off";
12          }
13      }
14      else
15      {
16          if (day <= 5 && day >= 1)
17          {
18              return "7:00";
19          }
20          else
21          {
22              return "10:00";
23          }
24      }
25  }
```

### Solução 5, CodeStateID `1733669`

```java
 1  public String alarmClock(int day, boolean vacation)
 2  {
 3  
 4      if (!vacation)
 5      	if (day > 0 && day < 6)
 6          	return "7:00";
 7      	else if (day == 0 || day == 6)
 8          	return "10:00";
 9      
10      if ((day > 0 && day < 6) && (vacation))
11          return "10:00";
12      else
13          return "off";
14  }
```

## Problema 233, `love6`

> The number 6 is a truly great number. Given two int values, a and b, return true if either one is 6. Or if their sum or difference is 6. Note: the function Math.abs(num) computes the absolute value of a number.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Invocação de método | 1 | 2 | `if(a == 6 \|\| b == 6 \|\| a + b == 6 \|\| Math.abs(a - b) == 6)` |
| Operações aritméticas básicas | 1 | 2 | `if(a == 6 \|\| b == 6 \|\| a + b == 6 \|\| Math.abs(a - b) == 6)` |
| Estruturas de instrução if-else | 2 | 3 a 21 | `if (a == 6 \|\| b == 6)`<br>`{`<br>`return true;`<br>`}`<br>`else`<br>`{`<br>`if (a + b == 6)`<br>`{`<br>`return true;`<br>`}`<br>`else if (Math.abs(a - b) == 6)`<br>`{`<br>`return true;`<br>`}`<br>`else`<br>`{`<br>`return false;`<br>`}`<br>`}` |
| Operadores lógicos e condicionais | 1 | 2 | `if(a == 6 \|\| b == 6 \|\| a + b == 6 \|\| Math.abs(a - b) == 6)` |
| Comparações numéricas | 1 | 2 | `if(a == 6 \|\| b == 6 \|\| a + b == 6 \|\| Math.abs(a - b) == 6)` |

### Solução 1, CodeStateID `1750385`

```java
1  public boolean love6(int a, int b) {
2      if(a == 6 || b == 6 || a + b == 6 || Math.abs(a - b) == 6)
3          return true;
4            
5      return false;
6  }
```

### Solução 2, CodeStateID `1724956`

```java
 1  public boolean love6(int a, int b)
 2  {
 3      if (a == 6 || b == 6)
 4      {
 5          return true;
 6      }
 7      else
 8      {
 9          if (a + b == 6)
10          {
11              return true;
12          }
13          else if (Math.abs(a - b) == 6)
14          {
15              return true;
16          }
17          else
18          {
19              return false;
20          }
21      }
22  }
```

### Solução 3, CodeStateID `1720474`

```java
 1  public boolean love6(int a, int b)
 2  {
 3      if (a == 6 || b == 6)
 4      {
 5          return true;
 6      }
 7      else
 8      {
 9          if (a - b == 6 || a + b == 6 || b - a == 6)
10          {
11              return true;
12          }
13          else
14          {
15              return false;
16          }
17      }
18  }
```

### Solução 4, CodeStateID `1750772`

```java
 1  public boolean love6(int a, int b)
 2  {
 3      int sum = a + b;
 4      int dif = a - b;
 5      int diff = b - a;
 6  	if (a == Math.abs(6))
 7          return true;
 8      if (b == Math.abs(6))
 9          return true;
10      if (sum == Math.abs(6))
11          return true;
12      if (dif == Math.abs(6))
13          return true;
14      if (diff == Math.abs(6))
15          return true;
16      return false;
17  }
18      
```

### Solução 5, CodeStateID `1747079`

```java
 1  public boolean love6(int a, int b)
 2  {
 3     if (a == 6 || b == 6)
 4     {
 5         return true;
 6     }
 7     else if (a + b == 6)
 8     {
 9     		return true;   
10     }
11     else if (a - b == 6)
12     {
13  		return true;
14     }
15     else if (b + a == 6)
16     {
17  		return true;
18     }
19     else if (b - a == 6)
20     {
21         return true;
22     }
23     else
24     {
25      	return false;   
26     }
27  }
```

## Problema 234, `cigarParty`

> When squirrels get together for a party, they like to have cigars. A squirrel party is successful when the number of cigars is between 40 and 60, inclusive. Unless it is the weekend, in which case there is no upper bound on the number of cigars. Return true if the party with the given values is successful, or false otherwise.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Métodos básicos de string | 5 | 168 | `if(str.substring(0,1).equals("f") && str.substring(str.length()-1,str.length()).equals("b"))` |
| Método Math.abs() | 5 | 228 | `if(Math.abs(a - b) >= 10 \|\| Math.abs(b - c) >= 10 \|\| Math.abs(a - c) >= 10)` |
| Operador de incremento de variável | 5 | 237 | `die1++;` |
| Operações aritméticas básicas | 5 | 54 | `return a+b;` |
| Operador de módulo | 5 | 95 | `if(n%11==0 \|\| n%11==1)` |
| Estruturas de instrução if-else | 5 | 87 a 90 | `if(n>=1 && n<=10)`<br>`return true;`<br>`else`<br>`return false;` |
| Operadores lógicos e condicionais | 2 | 2 | `return cigars >= 40 && (cigars <= 60 \|\| isWeekend);` |
| Precedência de operador e parênteses | 2 | 2 | `return cigars >= 40 && (cigars <= 60 \|\| isWeekend);` |
| Comparações numéricas | 2 | 2 | `return cigars >= 40 && (cigars <= 60 \|\| isWeekend);` |

### Solução 1, CodeStateID `1747897`

```java
1  public boolean cigarParty(int cigars, boolean isWeekend)
2  {
3      if(isWeekend)
4          return (cigars >= 40);
5          return (cigars >= 40 && cigars <= 60);
6      
7  }
```

### Solução 2, CodeStateID `1750948`

```java
1  public boolean cigarParty(int cigars, boolean isWeekend) {
2  		return cigars >= 40 && (cigars <= 60 || isWeekend);
3  	}
```

### Solução 3, CodeStateID `1720353`

```java
 1  public boolean cigarParty(int cigars, boolean isWeekend)
 2  {
 3      if (isWeekend)
 4      {
 5          if (cigars >= 40)
 6          {
 7              return true;
 8          }
 9          else
10          {
11              return false;
12          }
13      }
14      else
15      {
16          if(cigars >= 40 && cigars <= 60)
17          {
18              return true;
19          }
20          else
21          {
22              return false;
23          }
24      }
25  }
```

### Solução 4, CodeStateID `1731381`

```java
 1  public boolean cigarParty(int cigars, boolean isWeekend)
 2  {
 3    
 4      if (isWeekend == false)
 5      {
 6          
 7          if (cigars >= 40 && cigars <= 60)
 8          {
 9              
10              
11              return true;
12              
13              
14              
15          }
16          else
17          {
18              
19              return false;
20              
21              
22          }
23          
24          
25          
26          
27          
28          
29      }
30      
31      else
32      {
33          
34          
35          if (cigars >= 40)
36          {
37              
38              
39              return true;
40              
41              
42              
43          }
44          else
45          {
46              
47              return false;
48              
49              
50          }
51          
52          
53          
54          
55          
56          
57          
58          
59          
60          
61      }
62      
63      
64      
65    
66      
67  }
```

### Solução 5, CodeStateID `1750294`

```java
  1  public boolean cigarParty(int cigars, boolean isWeekend) {
  2    if(isWeekend && cigars >= 40)
  3      return true;
  4    else if(cigars >= 40 && cigars <=60)
  5      return true;
  6    else
  7      return false;
  8  }
  9  
 10  /////// dateFashion ////////////////////////////////////////////////////////////////
 11  public int dateFashion(int you, int date) {
 12    if(you<= 2 || date <= 2)
 13     return 0;
 14    else if(you>= 8 || date >= 8)
 15     return 2;
 16    else
 17     return 1;
 18  }
 19  
 20  /////// squirrelPlay ////////////////////////////////////////////////////////////////
 21  public boolean squirrelPlay(int temp, boolean isSummer) {
 22    if(isSummer && temp>=60 && temp<=100)
 23     return true;
 24    else if(temp>=60 && temp<=90)
 25     return true;
 26    else
 27     return false;
 28  }
 29  
 30  /////// caughtSpeeding ///////////////////////////////////////////////////////////////
 31  public int caughtSpeeding(int speed, boolean isBirthday) {
 32    if(isBirthday){
 33     if(speed<=65)
 34      return 0;
 35     else if(speed>=66 && speed<=85)
 36      return 1;
 37     else
 38      return 2;
 39    }
 40     
 41    if(speed<=60)
 42     return 0;
 43    else if(speed>=61 && speed<=80)
 44     return 1;
 45    else
 46     return 2;
 47  }
 48  
 49  /////// sortaSum //////////////////////////////////////////////////////////////////////
 50  public int sortaSum(int a, int b) {
 51    if(a+b>=10 && a+b<=19)
 52     return 20;
 53    else
 54     return a+b;
 55  }
 56  
 57  /////// alarmClock ////////////////////////////////////////////////////////////////////
 58  public String alarmClock(int day, boolean vacation) {
 59    if(vacation){
 60     if(day>=1 && day<=5)
 61      return "10:00";
 62     else
 63      return "off";
 64    }
 65    if(day>=1 && day<=5)
 66     return "7:00";
 67    else 
 68     return "10:00";
 69  }
 70  
 71  /////// love6 //////////////////////////////////////////////////////////////////////////
 72  public boolean love6(int a, int b) {
 73    if(a==6 || b==6 ||a+b==6 ||a-Math.abs(b)==6 || Math.abs(b)-Math.abs(a)==6)
 74     return true;
 75    else
 76     return false;
 77  }
 78  
 79  /////// in1To10 ////////////////////////////////////////////////////////////////////////
 80  public boolean in1To10(int n, boolean outsideMode) {
 81    if(outsideMode){
 82     if(n<=1 || n>=10)
 83      return true;
 84     else
 85      return false;
 86    }
 87    if(n>=1 && n<=10)
 88     return true;
 89    else
 90     return false;
 91  }
 92  
 93  /////// specialEleven ///////////////////////////////////////////////////////////////////
 94  public boolean specialEleven(int n) {
 95    if(n%11==0 || n%11==1)
 96     return true;
 97    else 
 98     return false;
 99  }
100  
101  /////// more20 ///////////////////////////////////////////////////////////////////////////
102  public boolean more20(int n) {
103    if(n%20==1 || n%20==2)
104     return true;
105    else
106     return false;
107  }
108  
109  /////// old35 /////////////////////////////////////////////////////////////////////////////
110  public boolean old35(int n) {
111    if(n%3==0 && n%5==0)
112     return false;
113    else if(n%3==0 || n%5==0)
114     return true;
115    else
116     return false;
117  }
118  
119  /////// less20 ////////////////////////////////////////////////////////////////////////////
120  public boolean less20(int n) {
121    int k =0;
122    if(n%20==18 || n%20==19)
123      return true;
124     else 
125      return false;
126  }
127  
128  /////// nearTen ///////////////////////////////////////////////////////////////////////////
129  public boolean nearTen(int num) {
130    if(num%10==2 || num%10==9||num%10==8||num%10==1||num%10==0)
131     return true;
132    else
133     return false;
134  }
135  
136  /////// teenSum ///////////////////////////////////////////////////////////////////////////
137  public int teenSum(int a, int b) {
138    if(a>=13 && a<=19 || b>=13 && b<=19)
139     return 19;
140    else
141     return a+b;
142  }
143  
144  /////// answerCell /////////////////////////////////////////////////////////////////////////
145  public boolean answerCell(boolean isMorning, boolean isMom, boolean isAsleep) {
146    if(isMorning && isMom && !isAsleep)
147     return true;
148    else if(!isAsleep && !isMorning)
149     return true;
150    else
151     return false;
152  }
153  
154  /////// teaParty ////////////////////////////////////////////////////////////////////////////
155  public int teaParty(int tea, int candy) {
156    if(tea<5 || candy <5)
157     return 0;
158    if(tea>= candy*2|| candy>= tea*2)
159     return 2;
160    else if(tea >= 5 && candy >=5)
161     return 1;
162    else
163     return 0;
164  }
165  
166  /////// fizzString ///////////////////////////////////////////////////////////////////////////
167  public String fizzString(String str) {
168    if(str.substring(0,1).equals("f") && str.substring(str.length()-1,str.length()).equals("b"))
169     return "FizzBuzz";
170    else if(str.substring(0,1).equals("f"))
171     return "Fizz";
172    else if(str.substring(str.length()-1,str.length()).equals("b"))
173     return "Buzz";
174    else
175     return str;
176  }
177  
178  /////// fizzString2 //////////////////////////////////////////////////////////////////////////
179  public String fizzString2(int n) {
180    if(n%3==0 && n%5==0)
181     return "FizzBuzz!";
182    else if(n%3==0)
183     return "Fizz!";
184    else if(n%5==0)
185     return "Buzz!";
186    else
187     return n+"!";
188  }
189  
190  /////// twoAsOne //////////////////////////////////////////////////////////////////////////////
191  public boolean twoAsOne(int a, int b, int c) {
192    if(a+b==c || b+c==a || a+c==b)
193     return true;
194    else
195     return false;
196  }
197  
198  /////// inOrder ////////////////////////////////////////////////////////////////////////////////
199  public boolean inOrder(int a, int b, int c, boolean bOk) {
200    if(bOk && c>b)
201     return true;
202    else if(!bOk && b>a && c>b)
203     return true;
204    else
205     return false;
206  }
207  
208  /////// inOrderEqual ////////////////////////////////////////////////////////////////////////////
209  public boolean inOrderEqual(int a, int b, int c, boolean equalOk) {
210    if(equalOk && b>=a && c>=b)
211     return true;
212    else if(!equalOk && b>a && c>b)
213     return true;
214    else
215     return false;
216  }
217  
218  /////// lastDigit ////////////////////////////////////////////////////////////////////////////////
219  public boolean lastDigit(int a, int b, int c) {
220    if(a%10==b%10 ||a%10==c%10||b%10==c%10)
221     return true;
222    else
223     return false;
224  }
225  
226  /////// lessBy10 //////////////////////////////////////////////////////////////////////////////////
227  public boolean lessBy10(int a, int b, int c) {
228    if(Math.abs(a - b) >= 10 || Math.abs(b - c) >= 10 || Math.abs(a - c) >= 10)
229     return true;
230    else
231     return false;
232  }
233  
234  /////// withoutDoubles /////////////////////////////////////////////////////////////////////////////
235  public int withoutDoubles(int die1, int die2, boolean noDoubles) {
236    if(noDoubles && die1==die2){
237     die1++;
238     if(die1>=7){
239      die1 = 1;
240      return die1+die2;
241      }
242     else
243      return die1+die2;
244     }
245     else
246      return die1+die2;
247  }
```

## Problema 235, `dateFashion`

> You and your date are trying to get a table at a restaurant. The parameter you is the stylishness of your clothes, in the range 0..10, and date is the stylishness of your date's clothes. Write a method that returns your chances of getting a table, encoded as an int value with 0 = no, 1 = maybe, 2 = yes. If either of you is very stylish, 8 or more, then the result is 2 (yes). With the exception that if either of you has style of 2 or less, then the result is 0 (no). Otherwise the result is 1 (maybe).

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Estruturas de instrução if-else | 1 | 5 a 12 | `if (you <= 2 \|\| date <= 2)`<br>`{`<br>`return 0;`<br>`}`<br>`else`<br>`{`<br>`return 2;`<br>`}` |
| Operadores lógicos e condicionais | 2 | 3 a 6 | `if (you <= 2 \|\| date <= 2)`<br>`return 0;`<br>`if (you >= 8 \|\| date >= 8)`<br>`return 2;` |
| Comparações numéricas | 2 | 3 a 6 | `if (you <= 2 \|\| date <= 2)`<br>`return 0;`<br>`if (you >= 8 \|\| date >= 8)`<br>`return 2;` |

### Solução 1, CodeStateID `1745611`

```java
 1  public int dateFashion(int you, int date)
 2  {
 3      if (you >= 8 || date >= 8)
 4      {
 5          if (you <= 2 || date <= 2)
 6          {
 7              return 0;
 8          }
 9          else
10          {
11              return 2;
12          }
13      }
14      else if (you <= 2 || date <= 2)
15      {
16          return 0;
17      }
18      else
19      {
20          return 1;
21      }
22  }
```

### Solução 2, CodeStateID `1728046`

```java
1  public int dateFashion(int you, int date)
2  {
3      if (you <= 2 || date <= 2)
4          return 0;
5      if (you >= 8 || date >= 8)
6          return 2;
7      return 1;
8  }
```

### Solução 3, CodeStateID `1720037`

```java
1  public int dateFashion(int you, int date)
2  {
3      if(you <= 2 || date <= 2)
4  		return 0;
5  	if(you >= 8 || date >= 8)
6  		return 2;
7  	return 1;
8  }
```

### Solução 4, CodeStateID `1750427`

```java
 1  public int dateFashion(int you, int date)
 2  {
 3    if(you <= 2 || date <= 2)
 4    {
 5     return 0;
 6    }
 7    if(you >= 9 || date >= 8)
 8    {
 9     return 2;
10    }
11    else
12    {
13     return 1;
14    }
15  }
16      
```

### Solução 5, CodeStateID `1734864`

```java
 1  public int dateFashion(int you, int date)
 2  {
 3      if (you > 7)
 4      {
 5          if (date > 2)
 6          {
 7              return 2;
 8          }
 9          else 
10          {
11              return 0;
12          }
13      }
14      else if (you > 2)
15      {
16          if (date > 7)
17          {
18              return 2;
19          }
20          else if (date > 2)
21          {
22              return 1;
23          }
24          else
25          {
26              return 0;
27          }
28      }
29      else
30      {
31          return 0;
32      }
33  }
```

## Problema 236, `greenTicket`

> You have a green lottery ticket, with ints a, b, and c on it. If the numbers are all different from each other, the result is 0. If all of the numbers are the same, the result is 20. If two of the numbers are the same, the result is 10.

| Conceito | Solução | Linhas | Trecho |
|---|---|---|---|
| Operações aritméticas básicas | 3 | 20 | `if (( a - b == b - c) && ( a - b == a - c )){` |
| Estruturas de instrução if-else | 2 | 11 a 18 | `if (a == c \|\| b == c)`<br>`{`<br>`return 10;`<br>`}`<br>`else`<br>`{`<br>`return 0;`<br>`}` |
| Operadores lógicos e condicionais | 1 | 3 a 7 | `if (a == b && b == c)`<br>`{`<br>`return 20;`<br>`}`<br>`if (a == b \|\| a == c \|\| b == c)` |
| Comparações numéricas | 1 | 3 | `if (a == b && b == c)` |

### Solução 1, CodeStateID `1727326`

```java
 1  public int greenTicket(int a, int b, int c)
 2  {
 3      if (a == b && b == c)
 4      {
 5      return 20;
 6      }
 7    if (a == b || a == c || b == c)
 8    {
 9      return 10;
10    }
11    else;
12      {
13      return 0;
14      }
15  }
```

### Solução 2, CodeStateID `1720913`

```java
 1  public int greenTicket(int a, int b, int c)
 2  {
 3      if (a == b) 
 4      {
 5          if (b == c)
 6          {
 7              return 20;
 8          }
 9          return 10;
10      }
11      if (a == c || b == c)
12      {
13          return 10;
14      }
15      else
16      {
17          return 0;
18      }
19  }
```

### Solução 3, CodeStateID `1746324`

```java
 1  public int greenTicket(int a, int b, int c)
 2  {
 3     // if ( a-b = 0)
 4   //   {
 5     //     if ( b-c = 0)
 6       //   {
 7         //     return("20");
 8        //  }
 9          //else  
10  //        {
11    //          return("10");
12      //    }
13  //    }
14  //    else
15  //    {
16   //       return("0");
17    //  }
18      
19        
20  	if (( a - b == b - c) && ( a - b == a - c )){
21      //    if (a - b == a - c){
22          	return(20);
23       //   }
24          
25     		}
26       else if ( a != b && b != c && c != a)
27       {
28              return(0);
29        }
30      else
31      {
32          return(10);
33      }
34      
35  
36  }
```

### Solução 4, CodeStateID `1727970`

```java
 1  public int greenTicket(int a, int b, int c)
 2  {
 3      if (a != b)
 4      {
 5          if (a != c)
 6          {
 7              if (b != c)
 8              {
 9                  return 0;
10              }
11              return 10;
12          }
13          return 10;
14      }
15      else
16      {
17          if (a == c)
18          {
19              if (b == c)
20              {
21                  return 20;
22              }
23              return 10;
24          }
25          return 10;
26      }
27  }
```

### Solução 5, CodeStateID `1737938`

```java
 1  public int greenTicket(int a, int b, int c)
 2  {
 3  	if(a == b)
 4  	{
 5  		if(b == c)
 6  			return 20;
 7  		return 10;
 8  	}
 9  	if(a == c || b == c)
10  		return 10;
11  	return 0;
12  }
```
