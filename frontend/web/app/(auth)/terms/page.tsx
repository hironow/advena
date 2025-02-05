export default function Page() {
  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-left sm:px-16">
          <h3 className="text-xl font-semibold dark:text-zinc-50">
            Terms of Service 利用規約
          </h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            <strong>
              BY USING MI-HO, YOU AGREE TO THE FOLLOWING TERMS OF SERVICE:
            </strong>{' '}
            <br />
            <strong>SERVICE DESCRIPTION:</strong> MI-HO IS AN AI-POWERED BOOK
            INFORMATION LOOKUP SERVICE THAT USES GOOGLE VERTEX AI TO PROVIDE
            INFORMATION ABOUT BOOKS. <br />
            <strong>DATA SOURCE:</strong> THE SERVICE OBTAINS BOOK DATA FROM THE
            NATIONAL DIET LIBRARY OF JAPAN. <br />
            <strong>ACCURACY OF AI RESPONSES:</strong> AI-GENERATED RESPONSES
            ARE NOT GUARANTEED TO BE ACCURATE. PLEASE USE YOUR OWN JUDGMENT WHEN
            INTERPRETING THE RESULTS. <br />
            <strong>LEGAL COMPLIANCE:</strong> THIS SERVICE IS OPERATED IN
            COMPLIANCE WITH JAPANESE LAW AND IS GOVERNED BY THE LAWS OF JAPAN.
            <br />
            <strong>AGE RECOMMENDATION:</strong> MI-HO IS RECOMMENDED FOR USERS
            AGED 13 AND ABOVE. IF YOU ARE UNDER 13, PLEASE USE THE SERVICE UNDER
            THE SUPERVISION OF A PARENT OR GUARDIAN.
          </p>

          <p className="text-sm text-gray-500 dark:text-zinc-400">
            <strong>
              mi-hoを利用することで、以下の利用規約に同意したことになります。
            </strong>
            <br />
            <strong>サービスの説明:</strong> mi-ho は、Google Vertex
            AIを活用した書籍情報検索サービスです。
            <br />
            <strong>データソース:</strong>{' '}
            本サービスでは、日本の国立国会図書館から書籍データを取得しています。
            <br />
            <strong>AI応答の正確性:</strong>{' '}
            AIが生成する回答は必ずしも正確であるとは限りません。結果をご利用の際はご自身の判断で行ってください。
            <br />
            <strong>法的順守:</strong>{' '}
            本サービスは日本の法律に準拠して運営されています。
            <br />
            <strong>年齢に関する推奨:</strong>{' '}
            mi-hoの利用は13歳以上の方に推奨されます。13歳未満の方は保護者の監督の下でご利用ください。
          </p>
        </div>
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-left sm:px-16">
          <h3 className="text-xl font-semibold dark:text-zinc-50">
            Privacy Policy プライバシーポリシー
          </h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            <strong>
              WE RESPECT YOUR PRIVACY. THIS PRIVACY POLICY EXPLAINS HOW MI-HO
              COLLECTS, USES, AND PROTECTS YOUR INFORMATION:
            </strong>{' '}
            <br />
            <strong>NO PERMANENT EMAIL STORAGE:</strong> WE DO NOT PERMANENTLY
            STORE EMAIL ADDRESSES IN OUR DATABASE. <br />
            <strong>USER INPUT DATA:</strong> WE STORE USER INPUTS TO THE AI
            (SUCH AS QUESTIONS OR SEARCH QUERIES) TO IMPROVE THE SERVICE.
            HOWEVER, WE DO NOT COLLECT PERSONAL DATA UNLESS YOU EXPLICITLY
            PROVIDE IT. <br />
            <strong>NO THIRD-PARTY SHARING:</strong> WE DO NOT SHARE YOUR DATA
            WITH ANY THIRD PARTIES. <br />
            <strong>AI RESPONSE RELIABILITY:</strong> PLEASE BE AWARE THAT
            AI-GENERATED RESPONSES MAY NOT ALWAYS BE RELIABLE OR CORRECT, AND
            USE THE INFORMATION AT YOUR OWN DISCRETION.
          </p>

          <p className="text-sm text-gray-500 dark:text-zinc-400">
            <strong>
              私たちは利用者のプライバシーを重視しています。本プライバシーポリシーでは、mi-hoが利用者の情報をどのように収集、使用、保護するかを説明します。
            </strong>
            <br />
            <strong>メールアドレスの非保存:</strong>{' '}
            本サービスでは、利用者のメールアドレスをデータベースに永久保存することはありません。
            <br />
            <strong>ユーザー入力データ:</strong> サービス向上のため、利用者が
            AIに入力した内容（質問や検索クエリ）は保存します。ただし、利用者が明示的に提供しない限り、個人データを収集することはありません。
            <br />
            <strong>第三者への非共有:</strong>{' '}
            私たちは利用者のデータを第三者と共有することはありません。
            <br />
            <strong>AI回答の信頼性:</strong>{' '}
            AIが生成する回答が常に正確または信頼できるとは限りません。得られた情報はご自身の裁量でご利用ください。
          </p>
        </div>
      </div>
    </div>
  );
}
