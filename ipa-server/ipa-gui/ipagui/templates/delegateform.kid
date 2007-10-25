<div xmlns:py="http://purl.org/kid/ns#"
  class="simpleroster">

  <?python searchurl = tg.url('/delegate/group_search') ?>

  <script type="text/javascript">

    function enterDoSearch(e, which_group) {
      var keyPressed;
      if (window.event) {
        keyPressed = window.event.keyCode;
      } else {
        keyPressed = e.which; 
      }

      if (keyPressed == 13) {
        return doSearch(which_group);
      } else {
        return true;
      }
    }

    function doSearch(which_group) {
      $(which_group + '_searchresults').update("Searching...");
      new Ajax.Updater(which_group + '_searchresults',
          '${searchurl}',
          {  asynchronous:true,
             parameters: { criteria: $(which_group + '_criteria').value,
                           which_group: which_group},
             evalScripts: true });
      return false;
    }

    function selectGroup(which_group, group_dn, group_cn) {
      group_dn_field = $('form_' + which_group + '_group_dn');
      group_cn_field = $('form_' + which_group + '_group_cn');
      group_cn_span = $(which_group + '_group_cn');

      group_dn_field.value = group_dn;
      group_cn_field.value = group_cn;
      group_cn_span.update(group_cn);

      new Effect.Fade($(which_group + '_searcharea'), {duration: 0.25});
      new Effect.Appear($(which_group + '_change_link'), {duration: 0.25});
    }

    function confirmDelete() {
      if (confirm("Are you sure you want to delete this delegation?")) {
        $('deleteform').submit();
      }
      return false;
    }
  </script>

  <form style="display:none" id='deleteform'
    method="post" action="${tg.url('/delegate/delete')}">
    <input type="hidden" name="acistr" value="${value.get('orig_acistr')}" />
  </form>

  <form action="${action}" name="${name}" method="${method}" class="tableform">

    <table class="formtable" cellpadding="2" cellspacing="0" border="0">
      <tr>
        <th>
          <input type="submit" class="submitbutton" name="submit"
                 value="${actionname} Delegation"/>
          <br/><br/>
        </th>
        <td>
          <input type="submit" class="submitbutton" name="submit"
                 value="Cancel ${actionname}"/>
          <br/><br/>
        </td>
        <td py:if='actionname == "Update"'>
          &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
          <input type="button" class="deletebutton"
                 value="Delete Delegation"
                 onclick="return confirmDelete();"
                 />
          <br/><br/>
        </td>
      </tr>
    </table>

    <div py:for="field in hidden_fields"
      py:replace="field.display(value_for(field), **params_for(field))" 
      />

    <table class="formtable" cellpadding="2" cellspacing="0" border="0">
      <tr>
        <th valign="top">
          <label class="fieldlabel" for="${delegate_fields.name.field_id}"
            py:content="delegate_fields.name.label" />:
        </th>
        <td>
          <span py:replace="delegate_fields.name.display(value_for(delegate_fields.name))" />
          <span py:if="tg.errors.get('name')" class="fielderror"
              py:content="tg.errors.get('name')" />
        </td>
      </tr>
      <tr>
        <th valign="top">
          <label class="fieldlabel" for="${delegate_fields.source_group_cn.field_id}"
            py:content="delegate_fields.source_group_cn.label" />:
        </th>
        <td>
          <div>
            <span id='source_group_cn'>${value_for(delegate_fields.source_group_cn)}</span>
            <a href="#" id='source_change_link'
              onclick="new Effect.Appear($('source_searcharea'), {duration: 0.25});
                       new Effect.Fade(this, {duration: 0.25});
                       return false;">change</a>
            <span py:if="tg.errors.get('source_group_dn')" class="fielderror"
                py:content="tg.errors.get('source_group_dn')" />
          </div>
          <div id="source_searcharea" style="display:none">
            <div>
              <input id="source_criteria" type="text"
                onkeypress="return enterDoSearch(event, 'source');" />
              <input type="button" value="Find"
                onclick="return doSearch('source');"
              />
            </div>
            <div id="source_searchresults">
            </div>
          </div>
        </td>
      </tr>
      <tr>
        <th valign="top">
          <label class="fieldlabel" for="${delegate_fields.attrs.field_id}"
            py:content="delegate_fields.attrs.label" />:
        </th>
        <td valign="top">
          <span py:if="tg.errors.get('attrs')" class="fielderror"
              py:content="tg.errors.get('attrs')" />
          <span py:replace="delegate_fields.attrs.display(value_for(delegate_fields.attrs))" />
        </td>
      </tr>
      <tr>
        <th valign="top">
          <label class="fieldlabel" for="${delegate_fields.dest_group_cn.field_id}"
            py:content="delegate_fields.dest_group_cn.label" />:
        </th>
        <td>
          <div>
            <span id='dest_group_cn'>${value_for(delegate_fields.dest_group_cn)}</span>
            <a href="#" id='dest_change_link'
              onclick="new Effect.Appear($('dest_searcharea'), {duration: 0.25});
                       new Effect.Fade(this, {duration: 0.25});
                       return false;">change</a>
            <span py:if="tg.errors.get('dest_group_dn')" class="fielderror"
                py:content="tg.errors.get('dest_group_dn')" />
          </div>
          <div id="dest_searcharea" style="display:none">
            <div>
              <input id="dest_criteria" type="text"
                onkeypress="return enterDoSearch(event, 'dest');" />
              <input type="button" value="Find"
                onclick="return doSearch('dest');"
              />
            </div>
            <div id="dest_searchresults">
            </div>
          </div>
        </td>
      </tr>
    </table>

    <table class="formtable" cellpadding="2" cellspacing="0" border="0">
      <tr>
        <th>
          <br/>
          <input type="submit" class="submitbutton" name="submit"
                 value="${actionname} Delegation"/>
        </th>
        <td>
          <br/>
          <input type="submit" class="submitbutton" name="submit"
                 value="Cancel ${actionname}"/>
        </td>
        <td py:if='actionname == "Update"'>
          <br/>
          &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
          <input type="button" class="deletebutton"
                 value="Delete Delegation"
                 onclick="return confirmDelete();"
                 />
        </td>
      </tr>
    </table>

  <script py:if="not value.get('source_group_dn')"
    type="text/javascript">
      new Effect.Appear($('source_searcharea'), {duration: 0.25});
      new Effect.Fade($('source_change_link'), {duration: 0.25});
  </script>
  <script py:if="not value.get('dest_group_dn')"
    type="text/javascript">
      new Effect.Appear($('dest_searcharea'), {duration: 0.25});
      new Effect.Fade($('dest_change_link'), {duration: 0.25});
  </script>

  </form>
</div>
